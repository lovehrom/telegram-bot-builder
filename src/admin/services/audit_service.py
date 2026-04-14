"""
Аудит-лог для admin API.
Логирует: кто (user_id), когда (timestamp), что (endpoint + method), результат (status code).
Хранит последние MAX_ENTRIES записей в памяти.
"""
import time
from collections import deque
from typing import Optional

MAX_ENTRIES = 1000

_entries: deque = deque(maxlen=MAX_ENTRIES)


def add_entry(
    user_id: Optional[str] = None,
    method: str = "",
    path: str = "",
    status_code: int = 0,
    client_ip: str = "",
) -> None:
    _entries.append({
        "timestamp": time.time(),
        "user_id": user_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "client_ip": client_ip,
    })


def get_entries(limit: int = 100) -> list:
    return list(_entries)[-limit:]
