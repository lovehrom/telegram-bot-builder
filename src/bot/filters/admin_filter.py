from aiogram.filters import BaseFilter
from aiogram.types import Message
from typing import List


class IsAdmin(BaseFilter):
    """Фильтр для проверки админа"""

    def __init__(self, admin_ids: List[int]):
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids
