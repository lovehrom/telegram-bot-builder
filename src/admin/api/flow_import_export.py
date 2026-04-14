"""
Export/Import Flows API
Позволяет экспортировать flows в JSON и импортировать обратно
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from src.database.session import get_async_session
from src.database.models import ConversationFlow, FlowBlock, FlowConnection
from src.admin.auth.dependencies import verify_api_token
from src.bot.handlers.flow_blocks.base import BLOCK_HANDLERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/flows", tags=["flows"])


class FlowExportSchema(BaseModel):
    """Schema for exported flow"""
    name: str
    description: Optional[str] = None
    is_global_menu: bool = False
    blocks: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    exported_at: str
    version: str = "1.0"


@router.get("/{flow_id}/export")
async def export_flow(
    flow_id: int,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """
    Экспортировать flow в JSON

    Возвращает JSON с:
    - Названием и описанием flow
    - Всеми блоками с их конфигурацией
    - Всеми соединениями
    - Метаданными экспорта
    """
    # Загружаем flow с блоками
    result = await session.execute(
        select(ConversationFlow)
        .options(selectinload(ConversationFlow.blocks))
        .where(ConversationFlow.id == flow_id)
    )
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Загружаем соединения
    connections_result = await session.execute(
        select(FlowConnection)
        .where(FlowConnection.flow_id == flow_id)
    )
    connections = connections_result.scalars().all()

    # Формируем экспорт
    export_data = FlowExportSchema(
        name=flow.name,
        description=flow.description,
        is_global_menu=flow.is_global_menu,
        blocks=[
            {
                "id": b.id,
                "block_type": b.block_type,
                "label": b.label,
                "config": b.config,
                "position_x": b.position_x,
                "position_y": b.position_y,
                "position": b.position
            }
            for b in flow.blocks
        ],
        connections=[
            {
                "id": c.id,
                "from_block_id": c.from_block_id,
                "to_block_id": c.to_block_id,
                "condition": c.condition,
                "condition_config": c.condition_config,
                "connection_style": c.connection_style
            }
            for c in connections
        ],
        exported_at=datetime.utcnow().isoformat(),
        version="1.0"
    )

    logger.info(f"Exported flow {flow_id}: {flow.name}")

    # Возвращаем с заголовком для скачивания
    return JSONResponse(
        content=export_data.model_dump(),
        headers={
            "Content-Disposition": f'attachment; filename="flow_{flow.name.replace(" ", "_")}.json"'
        }
    )


@router.post("/import")
async def import_flow(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """
    Импортировать flow из JSON файла

    Создаёт новый flow с блоками и соединениями из файла
    """
    try:
        # Читаем файл с ограничением размера (макс 1 МБ)
        content = await file.read(1_000_000)
        if len(content) >= 1_000_000:
            raise HTTPException(status_code=413, detail="Файл слишком большой. Максимальный размер: 1 МБ")
        data = json.loads(content)

        # Валидируем структуру
        if "name" not in data:
            raise HTTPException(status_code=400, detail="Invalid flow file: missing 'name'")

        if "blocks" not in data:
            raise HTTPException(status_code=400, detail="Invalid flow file: missing 'blocks'")

        # Создаём новый flow
        now = datetime.utcnow()
        new_flow = ConversationFlow(
            name=data["name"],
            description=data.get("description"),
            is_active=False,  # Импортированный flow не активен по умолчанию
            is_global_menu=data.get("is_global_menu", False),
            created_at=now,
            updated_at=now
        )
        session.add(new_flow)
        await session.flush()

        logger.info(f"Importing flow: {data['name']}")

        # Маппинг старых ID -> новых ID
        block_id_map = {}

        # Создаём блоки
        for block_data in data.get("blocks", []):
            block_type = block_data["block_type"]
            # Валидация block_type — отклоняем неизвестные типы (защита от XSS)
            if block_type not in BLOCK_HANDLERS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неизвестный тип блока при импорте: '{block_type}'. Доступные: {', '.join(sorted(BLOCK_HANDLERS.keys()))}"
                )
            new_block = FlowBlock(
                flow_id=new_flow.id,
                block_type=block_data["block_type"],
                label=block_data["label"],
                config=block_data.get("config", {}),
                position_x=block_data.get("position_x"),
                position_y=block_data.get("position_y"),
                position=block_data.get("position", 0)
            )
            session.add(new_block)
            await session.flush()
            block_id_map[block_data["id"]] = new_block.id

        # Создаём соединения
        connections_created = 0
        for conn_data in data.get("connections", []):
            from_id = block_id_map.get(conn_data["from_block_id"])
            to_id = block_id_map.get(conn_data["to_block_id"])

            if from_id and to_id:
                new_conn = FlowConnection(
                    flow_id=new_flow.id,
                    from_block_id=from_id,
                    to_block_id=to_id,
                    condition=conn_data.get("condition"),
                    condition_config=conn_data.get("condition_config", {}),
                    connection_style=conn_data.get("connection_style", {})
                )
                session.add(new_conn)
                connections_created += 1

        # Устанавливаем start_block_id (первый start блок или первый блок)
        if block_id_map:
            # Ищем start блок
            for block_data in data.get("blocks", []):
                if block_data["block_type"] == "start":
                    new_flow.start_block_id = block_id_map[block_data["id"]]
                    break
            else:
                # Если нет start блока, берём первый
                new_flow.start_block_id = list(block_id_map.values())[0]

        await session.commit()
        await session.refresh(new_flow)

        logger.info(f"Imported flow {new_flow.id}: {new_flow.name} with {len(block_id_map)} blocks, {connections_created} connections")

        return {
            "message": "Flow imported successfully",
            "flow_id": new_flow.id,
            "name": new_flow.name,
            "blocks_count": len(block_id_map),
            "connections_count": connections_created
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logger.error(f"Error importing flow: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка импорта flow. Проверьте формат файла и попробуйте снова.")


@router.post("/import-json")
async def import_flow_json(
    data: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """
    Импортировать flow из JSON (прямо в теле запроса)

    Альтернатива загрузке файла - можно отправить JSON напрямую
    """
    try:
        # Валидируем структуру
        if "name" not in data:
            raise HTTPException(status_code=400, detail="Invalid flow data: missing 'name'")

        if "blocks" not in data:
            raise HTTPException(status_code=400, detail="Invalid flow data: missing 'blocks'")

        # Создаём новый flow
        now = datetime.utcnow()
        new_flow = ConversationFlow(
            name=data["name"],
            description=data.get("description"),
            is_active=False,
            is_global_menu=data.get("is_global_menu", False),
            created_at=now,
            updated_at=now
        )
        session.add(new_flow)
        await session.flush()

        # Маппинг старых ID -> новых ID
        block_id_map = {}

        # Создаём блоки
        for block_data in data.get("blocks", []):
            block_type = block_data["block_type"]
            # Валидация block_type — отклоняем неизвестные типы (защита от XSS)
            if block_type not in BLOCK_HANDLERS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неизвестный тип блока при импорте: '{block_type}'. Доступные: {', '.join(sorted(BLOCK_HANDLERS.keys()))}"
                )
            new_block = FlowBlock(
                flow_id=new_flow.id,
                block_type=block_data["block_type"],
                label=block_data["label"],
                config=block_data.get("config", {}),
                position_x=block_data.get("position_x"),
                position_y=block_data.get("position_y"),
                position=block_data.get("position", 0)
            )
            session.add(new_block)
            await session.flush()
            block_id_map[block_data["id"]] = new_block.id

        # Создаём соединения
        connections_created = 0
        for conn_data in data.get("connections", []):
            from_id = block_id_map.get(conn_data["from_block_id"])
            to_id = block_id_map.get(conn_data["to_block_id"])

            if from_id and to_id:
                new_conn = FlowConnection(
                    flow_id=new_flow.id,
                    from_block_id=from_id,
                    to_block_id=to_id,
                    condition=conn_data.get("condition"),
                    condition_config=conn_data.get("condition_config", {}),
                    connection_style=conn_data.get("connection_style", {})
                )
                session.add(new_conn)
                connections_created += 1

        # Устанавливаем start_block_id
        if block_id_map:
            for block_data in data.get("blocks", []):
                if block_data["block_type"] == "start":
                    new_flow.start_block_id = block_id_map[block_data["id"]]
                    break
            else:
                new_flow.start_block_id = list(block_id_map.values())[0]

        await session.commit()
        await session.refresh(new_flow)

        logger.info(f"Imported flow {new_flow.id}: {new_flow.name} via JSON")

        return {
            "message": "Flow imported successfully",
            "flow_id": new_flow.id,
            "name": new_flow.name,
            "blocks_count": len(block_id_map),
            "connections_count": connections_created
        }

    except Exception as e:
        logger.error(f"Error importing flow: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка импорта flow из JSON. Проверьте данные и попробуйте снова.")


