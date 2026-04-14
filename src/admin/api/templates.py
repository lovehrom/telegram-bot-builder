from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.database.models.flow_template import FlowTemplate
from src.database.session import get_async_session
from src.admin.auth.dependencies import verify_api_token

router = APIRouter(prefix="/api/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    blocks_data: Dict[str, Any]
    connections_data: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    blocks_data: Dict[str, Any]
    connections_data: Optional[Dict[str, Any]]
    is_system: bool
    created_at: str


@router.get("/", response_model=List[TemplateResponse])
async def get_templates(session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Получить все шаблоны"""
    result = await session.execute(select(FlowTemplate).order_by(FlowTemplate.created_at.desc()))
    templates = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "blocks_data": t.blocks_data,
            "connections_data": t.connections_data,
            "is_system": t.is_system,
            "created_at": t.created_at.isoformat()
        }
        for t in templates
    ]


@router.post("/", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """Создать новый шаблон"""
    db_template = FlowTemplate(**template.model_dump())
    session.add(db_template)
    await session.commit()
    await session.refresh(db_template)

    return {
        "id": db_template.id,
        "name": db_template.name,
        "description": db_template.description,
        "blocks_data": db_template.blocks_data,
        "connections_data": db_template.connections_data,
        "is_system": db_template.is_system,
        "created_at": db_template.created_at.isoformat()
    }


@router.delete("/{template_id}")
async def delete_template(template_id: int, session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)):
    """Удалить шаблон (любой, включая системные)"""
    result = await session.execute(select(FlowTemplate).where(FlowTemplate.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    # Удаляем без проверки is_system
    await session.delete(template)
    await session.commit()
    return {"message": "Шаблон удалён"}
