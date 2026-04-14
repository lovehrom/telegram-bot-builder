from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import html
import logging

from src.database.session import get_async_session
from src.database.models import ConversationFlow, FlowBlock, FlowConnection, UserFlowState, FlowTemplate
from src.admin.auth.dependencies import verify_api_token
from src.bot.handlers.flow_blocks.base import BLOCK_HANDLERS, get_handler

logger = logging.getLogger(__name__)


async def validate_flow_before_activation(flow_id: int, session: AsyncSession) -> tuple[bool, list[str]]:
    """Валидировать flow перед активацией"""
    errors = []

    # Load flow with blocks
    result = await session.execute(
        select(ConversationFlow)
        .options(selectinload(ConversationFlow.blocks))
        .where(ConversationFlow.id == flow_id)
    )
    flow = result.scalar_one_or_none()

    if not flow:
        return False, ["Flow not found"]

    # Check: must have at least one block
    if not flow.blocks:
        errors.append("Flow must have at least one block")

    # #14: Не модифицируем flow в валидации — только проверяем
    if not flow.start_block_id:
        if not flow.blocks:
            errors.append("Flow must have a start block")
        else:
            errors.append("Flow must have start_block_id set")

    # Check: start_block must exist
    if flow.start_block_id:
        block_ids = {b.id for b in flow.blocks}
        if flow.start_block_id not in block_ids:
            errors.append(f"Start block {flow.start_block_id} not found in flow blocks")

    # Check: each block must have valid config for its type
    for block in flow.blocks:
        handler = get_handler(block.block_type)
        if not handler:
            errors.append(f"Block {block.id}: unknown block type '{block.block_type}'")
        elif handler:
            is_valid, error_msg = await handler.validate_config(block.config)
            if not is_valid:
                errors.append(f"Block {block.id} ({block.label}): {error_msg}")

    # Check: must have at least one connection (unless single block)
    conn_result = await session.execute(
        select(FlowConnection).where(FlowConnection.flow_id == flow_id)
    )
    connections = conn_result.scalars().all()
    if len(flow.blocks) > 1 and not connections:
        errors.append("Multi-block flow must have at least one connection")

    return len(errors) == 0, errors

router = APIRouter(prefix="/api/flows", tags=["flows"])


# Pydantic schemas for request/response
class FlowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="�������� ��������")
    description: Optional[str] = Field(None, max_length=1000, description="�������� ��������")
    is_active: bool = True
    is_global_menu: bool = False

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """����������� HTML � description"""
        if v is None:
            return None
        # Escape HTML entities
        return html.escape(v, quote=True)


class FlowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="�������� ��������")
    description: Optional[str] = Field(None, max_length=1000, description="�������� ��������")
    is_active: Optional[bool] = None
    is_global_menu: Optional[bool] = None
    start_block_id: Optional[int] = None

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """����������� HTML � description"""
        if v is None:
            return None
        # Escape HTML entities
        return html.escape(v, quote=True)


class BlockCreate(BaseModel):
    block_type: str = Field(..., min_length=1, max_length=50, description="Тип блока (например: text, video, quiz, start, end)")
    label: str = Field(..., min_length=1, max_length=255, description="Название блока")
    config: Dict[str, Any] = Field(default_factory=dict, description="Конфигурация блока")
    position_x: Optional[int] = Field(None, ge=0, description="Позиция X на холсте")
    position_y: Optional[int] = Field(None, ge=0, description="Позиция Y на холсте")
    position: int = Field(default=0, ge=0, description="Порядок блока")


class BlockUpdate(BaseModel):
    block_type: Optional[str] = None
    label: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    position: Optional[int] = None

    @field_validator('config')
    @classmethod
    def validate_config_is_dict(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """config ������ ���� �������"""
        if v is not None and not isinstance(v, dict):
            raise ValueError("config ������ ���� �������� (dict)")
        return v


# ������������ ���� config ��� ������� ���� �����
BLOCK_CONFIG_REQUIRED_FIELDS: Dict[str, List[str]] = {
    "text": ["message"],
    "video": ["video_url"],
    "image": ["image_url"],
    "quiz": ["question", "options"],
    "decision": ["question"],
    "menu": ["options"],
    "payment_gate": ["unpaid_message"],
    "create_payment": ["amount"],
    "delay": [],
    "start": [],
    "end": [],
    "confirmation": ["message"],
    "course_menu": [],
    "action": [],
    "input": ["prompt", "variable_name"],
    "random": [],
}


# #19: Общая функция валидации config блока
async def validate_block_config(block_type: str, config: dict) -> tuple[bool, str]:
    """Валидация config блока: обязательные поля + валидатор обработчика"""
    # Нормализация: admin API использует message, bot handlers используют text
    if block_type == "text" and "message" in config and "text" not in config:
        config["text"] = config["message"]

    required = BLOCK_CONFIG_REQUIRED_FIELDS.get(block_type, [])
    if required:
        missing = [f for f in required if f not in config]
        if missing:
            return False, f"Блок типа '{block_type}' требует обязательных полей config: {', '.join(missing)}"

    handler = get_handler(block_type)
    if handler:
        is_valid, error_msg = await handler.validate_config(config)
        if not is_valid:
            return False, f"Config validation failed for '{block_type}': {error_msg}"

    return True, ""


class ConnectionCreate(BaseModel):
    from_block_id: int
    to_block_id: int
    condition: Optional[str] = None
    condition_config: Dict[str, Any] = {}
    connection_style: Dict[str, Any] = {}


class FlowSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    is_global_menu: bool
    start_block_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlockSchema(BaseModel):
    id: int
    flow_id: int
    block_type: str
    label: str
    config: Dict[str, Any]
    position_x: Optional[int]
    position_y: Optional[int]
    position: int

    class Config:
        from_attributes = True


class ConnectionSchema(BaseModel):
    id: int
    flow_id: int
    from_block_id: int
    to_block_id: int
    condition: Optional[str]
    condition_config: Dict[str, Any]
    connection_style: Dict[str, Any]

    class Config:
        from_attributes = True


class FlowDetailSchema(FlowSchema):
    blocks: List[BlockSchema]
    connections: List[ConnectionSchema]


@router.get("", response_model=List[FlowSchema])
async def list_flows(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """Получить список всех flows с пагинацией"""
    result = await session.execute(
        select(ConversationFlow)
        .order_by(ConversationFlow.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    flows = result.scalars().all()
    return flows


@router.post("", response_model=FlowSchema)
async def create_flow(flow: FlowCreate, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Создать новый flow"""

    try:
        # Если создаем global menu - сбросить флаг у старого global menu
        if flow.is_global_menu:
            # Сброс флага global_menu у старых flows
            await session.execute(
                update(ConversationFlow)
                .where(ConversationFlow.is_global_menu == True)
                .values(is_global_menu=False)
            )

        now = datetime.utcnow()
        new_flow = ConversationFlow(
            name=flow.name,
            description=flow.description,
            is_active=flow.is_active,
            is_global_menu=flow.is_global_menu,
            created_at=now,
            updated_at=now
        )
        session.add(new_flow)
        await session.flush()
        logger.info(f"Created flow '{flow.name}' with ID {new_flow.id}, is_global_menu={flow.is_global_menu}")
        await session.commit()
        await session.refresh(new_flow)
        return new_flow

    except Exception as e:
        logger.error(f"Error creating flow: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.get("/{flow_id}", response_model=FlowDetailSchema)
async def get_flow(flow_id: int, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Получить flow со всеми блоками и соединениями"""
    result = await session.execute(
        select(ConversationFlow)
        .options(
            selectinload(ConversationFlow.blocks),
            selectinload(ConversationFlow.start_block)
        )
        .where(ConversationFlow.id == flow_id)
    )
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Get connections
    connections_result = await session.execute(
        select(FlowConnection)
        .where(FlowConnection.flow_id == flow_id)
    )
    connections = connections_result.scalars().all()

    return FlowDetailSchema(
        id=flow.id,
        name=flow.name,
        description=flow.description,
        is_active=flow.is_active,
        is_global_menu=flow.is_global_menu,
        start_block_id=flow.start_block_id,
        created_at=flow.created_at,
        updated_at=flow.updated_at,
        blocks=flow.blocks,
        connections=connections
    )


@router.put("/{flow_id}", response_model=FlowSchema)
async def update_flow(
    flow_id: int,
    flow: FlowUpdate,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """Обновить flow"""

    try:
        result = await session.execute(
            select(ConversationFlow).where(ConversationFlow.id == flow_id)
        )
        existing_flow = result.scalar_one_or_none()

        if not existing_flow:
            logger.warning(f"Flow {flow_id} not found when trying to update")
            raise HTTPException(status_code=404, detail="Flow not found")

        # Update only provided fields
        if flow.name is not None:
            existing_flow.name = flow.name
        if flow.description is not None:
            existing_flow.description = flow.description
        if flow.is_active is not None:
            existing_flow.is_active = flow.is_active
        if flow.start_block_id is not None:
            existing_flow.start_block_id = flow.start_block_id
        if flow.is_global_menu is not None:
            # If setting to global menu - reset flag on old global menu
            if flow.is_global_menu and not existing_flow.is_global_menu:
                result = await session.execute(
                    update(ConversationFlow)
                    .where(ConversationFlow.is_global_menu == True)
                    .where(ConversationFlow.id != flow_id)
                    .values(is_global_menu=False)
                )
            existing_flow.is_global_menu = flow.is_global_menu

        existing_flow.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(existing_flow)

        logger.info(f"Updated flow {flow_id}")
        return existing_flow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating flow {flow_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.delete("/{flow_id}")
async def delete_flow(flow_id: int, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Удалить flow (нельзя удалить активный)"""

    result = await session.execute(
        select(ConversationFlow).where(ConversationFlow.id == flow_id)
    )
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    if flow.is_active:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить активный flow. Сначала активируйте другой."
        )

    try:
        # 0. ������� �������� start_block_id (�� ��������� �� ����)
        flow.start_block_id = None
        await session.flush()

        # 1. #4: Завершить и удалить все UserFlowState
        await session.execute(
            update(UserFlowState).where(
                UserFlowState.flow_id == flow_id,
                UserFlowState.is_completed == False
            ).values(
                is_completed=True,
                completed_at=datetime.utcnow(),
                current_block_id=None
            )
        )
        await session.execute(
            delete(UserFlowState).where(UserFlowState.flow_id == flow_id)
        )
        logger.info(f"Очищены UserFlowState для flow {flow_id}")

        # 2. Удалить connections
        await session.execute(
            delete(FlowConnection).where(FlowConnection.flow_id == flow_id)
        )

        # 2. ������� blocks
        await session.execute(
            delete(FlowBlock).where(FlowBlock.flow_id == flow_id)
        )
        logger.info(f"Deleted blocks for flow {flow_id}")

        # 3. Потом удалить сам flow
        await session.execute(
            delete(ConversationFlow).where(ConversationFlow.id == flow_id)
        )
        logger.info(f"Deleted flow {flow_id}")

        await session.commit()
        return {"message": "Flow deleted successfully"}
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting flow {flow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.patch("/{flow_id}/activate", response_model=FlowSchema)
async def activate_flow(flow_id: int, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Переключить активацию flow (toggle: активен/неактивен)"""

    try:
        # Проверить что flow существует
        result = await session.execute(
            select(ConversationFlow).where(ConversationFlow.id == flow_id)
        )
        flow = result.scalar_one_or_none()

        if not flow:
            logger.warning(f"Flow {flow_id} not found when trying to toggle activation")
            raise HTTPException(status_code=404, detail="Flow not found")

        # Toggle активация flow
        new_active_state = not flow.is_active

        if new_active_state:
            # #14: Установить start_block_id перед валидацией, если не задан
            if not flow.start_block_id:
                blocks_result = await session.execute(
                    select(FlowBlock).where(FlowBlock.flow_id == flow_id)
                    .order_by(FlowBlock.position).limit(1)
                )
                first_block = blocks_result.scalar_one_or_none()
                if first_block:
                    flow.start_block_id = first_block.id
                    await session.flush()

            # Валидация перед активацией
            is_valid, errors = await validate_flow_before_activation(flow_id, session)

            if not is_valid:
                logger.warning(f"Flow {flow_id} validation failed: {errors}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Flow validation failed",
                        "errors": errors
                    }
                )

            # Если активируем - деактивировать все остальные flows
            await session.execute(
                update(ConversationFlow).values(is_active=False)
            )
            # Активировать выбранный
            await session.execute(
                update(ConversationFlow)
                .where(ConversationFlow.id == flow_id)
                .values(is_active=True, updated_at=datetime.utcnow())
            )
            logger.info(f"Flow {flow_id} activated")
        else:
            # Если деактивируем - просто деактивировать этот flow
            await session.execute(
                update(ConversationFlow)
                .where(ConversationFlow.id == flow_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            logger.info(f"Flow {flow_id} deactivated")

        await session.commit()

        # Вернуть обновленный flow
        result = await session.execute(
            select(ConversationFlow).where(ConversationFlow.id == flow_id)
        )
        flow = result.scalar_one()
        return flow

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error toggling flow {flow_id} activation: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.post("/from-template/{template_id}", response_model=FlowSchema)
async def create_flow_from_template(
    template_id: int,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """Создать flow из шаблона с блоками"""

    try:

        # Загрузить шаблон
        template_result = await session.execute(
            select(FlowTemplate).where(FlowTemplate.id == template_id)
        )
        template = template_result.scalar_one_or_none()

        if not template:
            logger.warning(f"Template {template_id} not found")
            raise HTTPException(status_code=404, detail="Template not found")

        # Создать flow
        flow = ConversationFlow(
            name=template.name,
            description=template.description,
            is_active=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(flow)
        await session.flush()  # Получаем flow.id

        logger.info(f"Created flow from template {template_id}, flow ID: {flow.id}")

        # Создать блоки из шаблона
        block_id_map = {}  # Старый ID -> Новый ID
        for block_data in template.blocks_data.get('blocks', []):
            new_block = FlowBlock(
                flow_id=flow.id,
                block_type=block_data['block_type'],
                label=block_data['label'],
                config=block_data.get('config', {}),
                position_x=block_data.get('position_x', 0),
                position_y=block_data.get('position_y', 0),
                position=block_data.get('position', 0)
            )
            session.add(new_block)
            await session.flush()
            block_id_map[block_data['id']] = new_block.id
            logger.info(f"Created block {new_block.id} from template block {block_data['id']}")

        # Создать связи
        connections_created = 0
        if template.connections_data:
            for conn in template.connections_data.get('connections', []):
                from_id = block_id_map.get(conn['from_block_id'])
                to_id = block_id_map.get(conn['to_block_id'])

                if from_id and to_id:
                    new_conn = FlowConnection(
                        flow_id=flow.id,
                        from_block_id=from_id,
                        to_block_id=to_id,
                        condition=conn.get('condition'),
                        condition_config=conn.get('condition_config', {}),
                        connection_style=conn.get('connection_style', {})
                    )
                    session.add(new_conn)
                    connections_created += 1

        logger.info(f"Created {connections_created} connections for flow {flow.id}")

        await session.commit()
        await session.refresh(flow)

        # Set first block as start_block_id if available
        if block_id_map:
            flow.start_block_id = list(block_id_map.values())[0]
            await session.commit()
            await session.refresh(flow)

        return flow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating flow from template {template_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.post("/{flow_id}/blocks", response_model=BlockSchema)
async def create_block(
    flow_id: int,
    block: BlockCreate,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """Создать блок в flow"""

    try:
        # Check if flow exists
        flow_result = await session.execute(
            select(ConversationFlow).where(ConversationFlow.id == flow_id)
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            logger.warning(f"Flow {flow_id} not found when creating block")
            raise HTTPException(status_code=404, detail="Flow not found")

        # Runtime проверка типа блока (избежание circular dependency с Pydantic validator)
        if block.block_type not in BLOCK_HANDLERS:
            available = ', '.join(sorted(BLOCK_HANDLERS.keys()))
            raise HTTPException(status_code=400, detail=f"Неизвестный тип блока: '{block.block_type}'. Доступные типы: {available}")

        # Validate block data
        if not block.block_type:
            logger.error(f"block_type is required but was empty for flow {flow_id}")
            raise HTTPException(status_code=400, detail="block_type is required")

        if not block.label:
            logger.error(f"label is required but was empty for flow {flow_id}")
            raise HTTPException(status_code=400, detail="label is required")

                # #19: Используем общую функцию валидации
        is_valid, validation_error = await validate_block_config(block.block_type, block.config)
        if not is_valid:
            raise HTTPException(status_code=422, detail=validation_error)

        # Create block with proper field mapping
        new_block = FlowBlock(
            flow_id=flow_id,
            block_type=block.block_type,
            label=block.label,
            config=block.config if block.config else {},
            position_x=block.position_x,
            position_y=block.position_y,
            position=block.position
        )

        session.add(new_block)
        await session.flush()  # Flush to get the ID before commit

        logger.info(f"Committed block {new_block.id} to database, type: '{block.block_type}', label: '{block.label}', flow_id: {flow_id}")

        await session.commit()
        await session.refresh(new_block)

        logger.info(f"Created block {new_block.id} of type '{block.block_type}' for flow {flow_id}")

        return new_block

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Validation errors from Pydantic
        logger.error(f"Validation error creating block for flow {flow_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=400, detail="���������� ������ �������. ���������� � ��������������.")
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error creating block for flow {flow_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.put("/blocks/{block_id}", response_model=BlockSchema)
async def update_block(
    block_id: int,
    block: BlockUpdate,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """Обновить блок"""

    try:
        result = await session.execute(
            select(FlowBlock).where(FlowBlock.id == block_id)
        )
        existing_block = result.scalar_one_or_none()

        if not existing_block:
            logger.warning(f"Block {block_id} not found when trying to update")
            raise HTTPException(status_code=404, detail="Block not found")

        # Update only provided fields
        if block.block_type is not None:
            # #18: Валидация block_type
            if block.block_type not in BLOCK_HANDLERS:
                available = ', '.join(sorted(BLOCK_HANDLERS.keys()))
                raise HTTPException(status_code=400, detail=f"Неизвестный тип блока: '{block.block_type}'. Доступные типы: {available}")
            existing_block.block_type = block.block_type
        if block.label is not None:
            existing_block.label = block.label
        if block.config is not None:
            existing_block.config = block.config
        # ��������� ������������ ����� config ��� ����������
        if block.config is not None:
            # #19: Общая валидация config
            check_type = block.block_type or existing_block.block_type
            is_valid, validation_error = await validate_block_config(check_type, block.config if block.config else existing_block.config)
            if not is_valid:
                raise HTTPException(status_code=422, detail=validation_error)


        if block.position_x is not None:
            existing_block.position_x = block.position_x
        if block.position_y is not None:
            existing_block.position_y = block.position_y
        if block.position is not None:
            existing_block.position = block.position

        existing_block.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(existing_block)

        logger.info(f"Updated block {block_id}")
        return existing_block

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating block {block_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.delete("/blocks/{block_id}")
async def delete_block(block_id: int, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Удалить блок"""
    result = await session.execute(
        select(FlowBlock).where(FlowBlock.id == block_id)
    )
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    # #13: Удалить все соединения с этим блоком перед удалением
    await session.execute(
        delete(FlowConnection).where(
            (FlowConnection.from_block_id == block_id) |
            (FlowConnection.to_block_id == block_id)
        )
    )
    logger.info(f"Удалены соединения для блока {block_id}")

    await session.delete(block)
    await session.commit()
    return {"message": "Block deleted successfully"}


@router.post("/{flow_id}/connections", response_model=ConnectionSchema)
async def create_connection(
    flow_id: int,
    connection: ConnectionCreate,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """Создать соединение между блоками"""

    try:
        # Check if flow exists
        flow_result = await session.execute(
            select(ConversationFlow).where(ConversationFlow.id == flow_id)
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            logger.warning(f"Flow {flow_id} not found when creating connection")
            raise HTTPException(status_code=404, detail="Flow not found")

        # Проверка: нельзя создать связь блока с самим собой
        if connection.from_block_id == connection.to_block_id:
            raise HTTPException(status_code=400, detail="Нельзя создать связь блока с самим собой")

        # #26: Проверка на циклические связи (BFS от to_block до from_block)
        # Используем raw SQL для надёжности (ORM запросы могут не видеть данные из других транзакций)
        from sqlalchemy import text
        visited = set()
        queue = [connection.to_block_id]
        cycle_found = False
        while queue:
            current = queue.pop(0)
            if current == connection.from_block_id:
                cycle_found = True
                break
            if current in visited:
                continue
            visited.add(current)
            # Raw SQL — ищем все исходящие связи из current блока
            result = await session.execute(
                text("SELECT to_block_id FROM flow_connections WHERE from_block_id = :bid AND flow_id = :fid"),
                {"bid": current, "fid": flow_id}
            )
            for (to_id,) in result.fetchall():
                if to_id not in visited:
                    queue.append(to_id)
        if cycle_found:
            raise HTTPException(status_code=400, detail="Создание этой связи приведёт к циклу в графе flow")

        # Check if blocks exist
        blocks_result = await session.execute(
            select(FlowBlock).where(
                FlowBlock.id.in_([connection.from_block_id, connection.to_block_id])
            )
        )
        blocks = blocks_result.scalars().all()

        if len(blocks) != 2:
            logger.error(f"Blocks not found for connection: from={connection.from_block_id}, to={connection.to_block_id}")
            raise HTTPException(status_code=404, detail="One or both blocks not found")

        # Validate that both blocks belong to the same flow
        for block in blocks:
            if block.flow_id != flow_id:
                logger.error(f"Block {block.id} belongs to flow {block.flow_id}, not {flow_id}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Block {block.id} does not belong to this flow"
                )

        # Check for duplicate connections
        duplicate_check = await session.execute(
            select(FlowConnection).where(
                FlowConnection.flow_id == flow_id,
                FlowConnection.from_block_id == connection.from_block_id,
                FlowConnection.to_block_id == connection.to_block_id,
                FlowConnection.condition == connection.condition
            )
        )
        duplicate = duplicate_check.scalar_one_or_none()
        
        if duplicate:
            logger.warning(f"Duplicate connection already exists: from={connection.from_block_id}, to={connection.to_block_id}, condition={connection.condition}")
            raise HTTPException(
                status_code=409,
                detail="Connection already exists"
            )

        new_connection = FlowConnection(
            flow_id=flow_id,
            from_block_id=connection.from_block_id,
            to_block_id=connection.to_block_id,
            condition=connection.condition,
            condition_config=connection.condition_config,
            connection_style=connection.connection_style
        )
        session.add(new_connection)
        await session.flush()

        logger.info(f"Created connection from block {connection.from_block_id} to {connection.to_block_id}")

        await session.commit()
        await session.refresh(new_connection)
        return new_connection

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating connection for flow {flow_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.delete("/connections/{connection_id}")
async def delete_connection(connection_id: int, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Удалить соединение"""
    result = await session.execute(
        select(FlowConnection).where(FlowConnection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    await session.delete(connection)
    await session.commit()
    return {"message": "Connection deleted successfully"}


@router.get("/{flow_id}/connections", response_model=List[ConnectionSchema])
async def get_flow_connections(flow_id: int, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Получить все соединения для flow"""
    # Check if flow exists
    flow_result = await session.execute(
        select(ConversationFlow).where(ConversationFlow.id == flow_id)
    )
    flow = flow_result.scalar_one_or_none()

    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Get connections
    connections_result = await session.execute(
        select(FlowConnection)
        .where(FlowConnection.flow_id == flow_id)
        .order_by(FlowConnection.id)
    )
    connections = connections_result.scalars().all()

    return connections


@router.get("/{flow_id}/validate")
async def validate_flow(flow_id: int, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Валидировать структуру flow"""

    try:
        is_valid, errors = await validate_flow_before_activation(flow_id, session)

        return {
            "flow_id": flow_id,
            "is_valid": is_valid,
            "errors": errors,
            "error_count": len(errors)
        }

    except Exception as e:
        logger.error(f"Error validating flow {flow_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )


@router.post("/{flow_id}/duplicate", response_model=FlowSchema)
async def duplicate_flow(
    flow_id: int,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """
    Дублировать flow (копировать)

    Создаёт полную копию flow со всеми блоками и соединениями
    """

    try:
        # Загрузить исходный flow с блоками
        result = await session.execute(
            select(ConversationFlow)
            .options(selectinload(ConversationFlow.blocks))
            .where(ConversationFlow.id == flow_id)
        )
        original_flow = result.scalar_one_or_none()

        if not original_flow:
            logger.warning(f"Flow {flow_id} not found for duplication")
            raise HTTPException(status_code=404, detail="Flow not found")

        # Загрузить соединения
        connections_result = await session.execute(
            select(FlowConnection)
            .where(FlowConnection.flow_id == flow_id)
        )
        original_connections = connections_result.scalars().all()

        # Создать новый flow (копия)
        now = datetime.utcnow()
        new_flow = ConversationFlow(
            name=f"{original_flow.name} (copy)",
            description=original_flow.description,
            is_active=False,  # Копия не активна по умолчанию
            is_global_menu=False,  # Копия не может быть global menu
            created_at=now,
            updated_at=now
        )
        session.add(new_flow)
        await session.flush()

        logger.info(f"Duplicating flow {flow_id} to new flow {new_flow.id}")

        # Маппинг старых ID -> новых ID
        block_id_map = {}

        # Создать блоки (копии)
        for original_block in original_flow.blocks:
            new_block = FlowBlock(
                flow_id=new_flow.id,
                block_type=original_block.block_type,
                label=original_block.label,
                config=original_block.config.copy() if original_block.config else {},
                position_x=original_block.position_x,
                position_y=original_block.position_y,
                position=original_block.position
            )
            session.add(new_block)
            await session.flush()
            block_id_map[original_block.id] = new_block.id

        # Создать соединения (копии)
        connections_created = 0
        for original_conn in original_connections:
            from_id = block_id_map.get(original_conn.from_block_id)
            to_id = block_id_map.get(original_conn.to_block_id)

            if from_id and to_id:
                new_conn = FlowConnection(
                    flow_id=new_flow.id,
                    from_block_id=from_id,
                    to_block_id=to_id,
                    condition=original_conn.condition,
                    condition_config=original_conn.condition_config.copy() if original_conn.condition_config else {},
                    connection_style=original_conn.connection_style.copy() if original_conn.connection_style else {}
                )
                session.add(new_conn)
                connections_created += 1

        # Установить start_block_id
        if original_flow.start_block_id and original_flow.start_block_id in block_id_map:
            new_flow.start_block_id = block_id_map[original_flow.start_block_id]

        await session.commit()
        await session.refresh(new_flow)

        logger.info(f"Duplicated flow {flow_id} -> {new_flow.id}: {new_flow.name} with {len(block_id_map)} blocks, {connections_created} connections")

        return new_flow

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating flow {flow_id}: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="���������� ������ �������. ���������� � ��������������."
        )

