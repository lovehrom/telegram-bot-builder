from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from src.database.session import get_async_session
from src.database.models import ConversationFlow, FlowBlock, FlowConnection
from src.admin.auth.dependencies import verify_api_token

router = APIRouter(prefix="/api/global-menu", tags=["global-menu"])
logger = logging.getLogger(__name__)


# Simplified schemas for Global Menu
class GlobalMenuButton(BaseModel):
    label: str = Field(..., min_length=1, max_length=64, description="Текст на кнопке")
    action_type: str = Field(..., description="Тип действия: launch_flow или callback")
    target_flow_name: Optional[str] = Field(None, description="Название flow для запуска (если action_type=launch_flow)")
    target_callback: Optional[str] = Field(None, description="Callback функция (если action_type=callback)")


class GlobalMenuConfig(BaseModel):
    buttons: List[GlobalMenuButton] = []


class GlobalMenuResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    buttons: List[GlobalMenuButton]


@router.get("", response_model=GlobalMenuResponse)
async def get_global_menu(session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Получить текущий Global Menu"""
    result = await session.execute(
        select(ConversationFlow).where(ConversationFlow.is_global_menu == True)
    )
    global_flow = result.scalar_one_or_none()

    if not global_flow:
        # Вернуть пустой глобальный меню
        return GlobalMenuResponse(
            id=0,
            name="",
            description="",
            is_active=False,
            buttons=[]
        )

    # Загрузить menu blocks
    menu_blocks_result = await session.execute(
        select(FlowBlock).where(
            FlowBlock.flow_id == global_flow.id,
            FlowBlock.block_type == "menu"
        ).order_by(FlowBlock.position)
    )
    menu_blocks = menu_blocks_result.scalars().all()

    # Собрать кнопки из всех menu blocks с is_global=true
    buttons = []
    for block in menu_blocks:
        block_buttons = block.config.get('buttons', [])
        is_global = block.config.get('is_global', False)

        if is_global:
            for btn in block_buttons:
                action = btn.get('action', 'launch_flow')
                target = btn.get('target', '')

                if action == 'launch_flow':
                    buttons.append(GlobalMenuButton(
                        label=btn.get('label', ''),
                        action_type='launch_flow',
                        target_flow_name=target,
                        target_callback=None
                    ))
                elif action == 'callback':
                    buttons.append(GlobalMenuButton(
                        label=btn.get('label', ''),
                        action_type='callback',
                        target_flow_name=None,
                        target_callback=target
                    ))

    return GlobalMenuResponse(
        id=global_flow.id,
        name=global_flow.name,
        description=global_flow.description,
        is_active=global_flow.is_active,
        buttons=buttons
    )


@router.put("", response_model=GlobalMenuResponse)
async def update_global_menu(menu_config: GlobalMenuConfig, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Создать или обновить Global Menu"""
    try:
        # Найти существующий global menu
        result = await session.execute(
            select(ConversationFlow).where(ConversationFlow.is_global_menu == True)
        )
        global_flow = result.scalar_one_or_none()

        if not global_flow:
            # Создать новый global menu
            now = datetime.utcnow()
            global_flow = ConversationFlow(
                name="Главное меню",
                description="Глобальное меню бота",
                is_active=True,
                is_global_menu=True,
                created_at=now,
                updated_at=now
            )
            session.add(global_flow)
            await session.flush()
            logger.info(f"Created new global menu flow with ID {global_flow.id}")
        else:
            # Удалить старые menu blocks и connections
            # Сначала удалить connections
            await session.execute(
                delete(FlowConnection).where(FlowConnection.flow_id == global_flow.id)
            )
            # Потом удалить menu blocks
            await session.execute(
                delete(FlowBlock).where(
                    FlowBlock.flow_id == global_flow.id,
                    FlowBlock.block_type == "menu"
                )
            )
            logger.info(f"Cleared old menu blocks from global menu {global_flow.id}")

        # Создать новые menu blocks на основе конфигурации
        # Все кнопки в один блок для простоты
        if menu_config.buttons:
            buttons_config = []
            for btn in menu_config.buttons:
                if btn.action_type == 'launch_flow':
                    buttons_config.append({
                        'label': btn.label,
                        'action': 'launch_flow',
                        'target': btn.target_flow_name
                    })
                elif btn.action_type == 'callback':
                    buttons_config.append({
                        'label': btn.label,
                        'action': 'callback',
                        'target': btn.target_callback
                    })

            new_block = FlowBlock(
                flow_id=global_flow.id,
                block_type="menu",
                label="Main Menu",
                config={
                    'text': 'Главное меню',
                    'is_global': True,
                    'buttons': buttons_config
                },
                position_x=100,
                position_y=100,
                position=0
            )
            session.add(new_block)
            await session.flush()
            logger.info(f"Created menu block with {len(buttons_config)} buttons")

        global_flow.updated_at = datetime.utcnow()
        await session.commit()

        # Вернуть обновленный global menu
        return await get_global_menu(session)

    except Exception as e:
        logger.error(f"Error updating global menu: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера. Обратитесь к администратору."
        )


@router.delete("")
async def delete_global_menu(session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Удалить Global Menu"""
    result = await session.execute(
        select(ConversationFlow).where(ConversationFlow.is_global_menu == True)
    )
    global_flow = result.scalar_one_or_none()

    if not global_flow:
        raise HTTPException(status_code=404, detail="Global menu not found")

    try:
        # Удалить connections
        await session.execute(
            delete(FlowConnection).where(FlowConnection.flow_id == global_flow.id)
        )
        # Удалить blocks
        await session.execute(
            delete(FlowBlock).where(FlowBlock.flow_id == global_flow.id)
        )
        # Удалить flow
        await session.execute(
            delete(ConversationFlow).where(ConversationFlow.id == global_flow.id)
        )

        await session.commit()
        logger.info(f"Deleted global menu flow {global_flow.id}")
        return {"message": "Global menu deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting global menu: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера. Обратитесь к администратору."
        )


