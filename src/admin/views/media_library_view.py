from sqladmin import ModelView

from src.database.models import MediaLibrary


class MediaLibraryView(ModelView, model=MediaLibrary):
    """Админ-вью для управления медиа библиотекой"""
    
    # Русские названия
    name = "Медиа файл"
    name_plural = "Медиа библиотека (Media Library)"
    icon = "fa-image"
    
    column_list = [
        MediaLibrary.id,
        MediaLibrary.file_type,
        MediaLibrary.file_name,
        MediaLibrary.description,
        MediaLibrary.uploaded_at,
        MediaLibrary.is_active
    ]

    column_labels = {
        "file_id": "File ID",
        "file_type": "Тип файла",
        "file_name": "Имя файла",
        "uploaded_by": "Загрузил (TG ID)",
        "uploaded_at": "Загружен",
        "description": "Описание",
        "is_active": "Активен"
    }

    form_columns = [
        MediaLibrary.file_id,
        MediaLibrary.file_type,
        MediaLibrary.file_name,
        MediaLibrary.description,
        MediaLibrary.is_active
    ]

    column_sortable_list = [
        MediaLibrary.id,
        MediaLibrary.file_type,
        MediaLibrary.uploaded_at
    ]

    column_default_sort = (MediaLibrary.uploaded_at, True)  # desc
