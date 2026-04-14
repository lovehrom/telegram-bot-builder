import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.session import get_async_session
from src.database.models import MediaLibrary
from src.admin.auth.dependencies import verify_api_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("")
async def get_media(
    file_type: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    authenticated: bool = Depends(verify_api_token)
):
    """
    Получить список медиа файлов (защищено API токеном)

    Args:
        file_type: Фильтр по типу файла (photo, video, document)
        session: Database session

    Headers:
        X-API-Token: Ваш API токен (настраивается в .env как API_TOKEN)
    """
    # Валидация file_type
    if file_type and file_type not in ["photo", "video", "document"]:
        logger.warning(f"Invalid file_type filter: {file_type}")
        raise HTTPException(status_code=400, detail=f"Invalid file_type: {file_type}. Must be one of: photo, video, document")

    query = select(MediaLibrary).where(MediaLibrary.is_active == True)

    if file_type:
        query = query.where(MediaLibrary.file_type == file_type)

    query = query.order_by(MediaLibrary.uploaded_at.desc())

    result = await session.execute(query)
    media_items = result.scalars().all()

    logger.debug(f"Retrieved {len(media_items)} media items (filter: {file_type})")

    return [
        {
            "id": item.id,
            "file_id": item.file_id,
            "file_type": item.file_type,
            "file_name": item.file_name,
            "description": item.description,
            "uploaded_at": item.uploaded_at.isoformat()
        }
        for item in media_items
    ]
