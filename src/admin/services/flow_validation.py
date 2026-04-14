"""
Flow validation utilities
Валидация структуры conversation flows
"""
from typing import List, Dict, Set, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from src.database.models import ConversationFlow, FlowBlock, FlowConnection

logger = logging.getLogger(__name__)


class FlowValidationError(Exception):
    """Ошибка валидации flow"""
    def __init__(self, message: str, details: Optional[List[str]] = None):
        self.message = message
        self.details = details or []
        super().__init__(message)


async def validate_flow_structure(
    flow: ConversationFlow,
    blocks: List[FlowBlock],
    connections: List[FlowConnection]
) -> Tuple[bool, List[str]]:
    """
    Валидировать структуру flow

    Returns:
        (is_valid, errors)
    """
    errors = []

    if not blocks:
        errors.append("Flow has no blocks")
        return False, errors

    # 1. Проверка наличия start блока
    start_blocks = [b for b in blocks if b.block_type == 'start']
    if len(start_blocks) == 0:
        errors.append("Flow must have at least one 'start' block")
    elif len(start_blocks) > 1:
        errors.append(f"Flow has {len(start_blocks)} 'start' blocks, should have exactly 1")

    # 2. Проверка наличия end блока
    end_blocks = [b for b in blocks if b.block_type == 'end']
    if len(end_blocks) == 0:
        errors.append("Flow must have at least one 'end' block")

    # 3. Проверка start_block_id
    if flow.start_block_id:
        start_block_exists = any(b.id == flow.start_block_id for b in blocks)
        if not start_block_exists:
            errors.append(f"start_block_id {flow.start_block_id} references non-existent block")
        else:
            start_block = next((b for b in blocks if b.id == flow.start_block_id), None)
            if start_block and start_block.block_type != 'start':
                errors.append(f"start_block_id references '{start_block.block_type}' block, should be 'start' block")
    elif start_blocks:
        # Если есть start блоки, но start_block_id не установлен
        errors.append("start_block_id is not set, but start blocks exist")

    # 4. Проверка на циклы
    cycle_errors = await _check_for_cycles(blocks, connections)
    errors.extend(cycle_errors)

    # 5. Проверка что все пути ведут к end блоку
    path_errors = await _check_paths_to_end(blocks, connections)
    errors.extend(path_errors)

    # 6. Проверка orphaned блоков (блоки без входящих соединений, кроме start)
    orphan_errors = _check_orphaned_blocks(blocks, connections)
    errors.extend(orphan_errors)

    # 7. Проверка что все блоки имеют правильные типы соединений
    connection_errors = _validate_block_connections(blocks, connections)
    errors.extend(connection_errors)

    is_valid = len(errors) == 0
    return is_valid, errors


async def _check_for_cycles(
    blocks: List[FlowBlock],
    connections: List[FlowConnection]
) -> List[str]:
    """
    Проверить наличие циклов в графе

    Использует DFS для обнаружения циклов
    """
    errors = []

    if not blocks or not connections:
        return errors

    # Строим граф
    graph: Dict[int, List[int]] = {}
    block_ids = {b.id for b in blocks}

    for block_id in block_ids:
        graph[block_id] = []

    for conn in connections:
        if conn.from_block_id in block_ids and conn.to_block_id in block_ids:
            graph[conn.from_block_id].append(conn.to_block_id)

    # DFS для обнаружения циклов
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {block_id: WHITE for block_id in block_ids}

    def dfs(node: int, path: List[int]) -> bool:
        """Возвращает True если найден цикл"""
        color[node] = GRAY
        path.append(node)

        for neighbor in graph.get(node, []):
            if color[neighbor] == GRAY:
                # Найден цикл
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                errors.append(f"Cycle detected: {' -> '.join(map(str, cycle))}")
                return True
            elif color[neighbor] == WHITE:
                if dfs(neighbor, path):
                    return True

        path.pop()
        color[node] = BLACK
        return False

    for block_id in block_ids:
        if color[block_id] == WHITE:
            dfs(block_id, [])

    return errors


async def _check_paths_to_end(
    blocks: List[FlowBlock],
    connections: List[FlowConnection]
) -> List[str]:
    """
    Проверить что все пути ведут к end блоку

    Находит блоки от которых невозможно добраться до end блока
    """
    errors = []

    if not blocks:
        return errors

    end_block_ids = {b.id for b in blocks if b.block_type == 'end'}
    if not end_block_ids:
        return errors  # Ошибка уже добавлена выше

    # Строим граф
    graph: Dict[int, List[int]] = {}
    block_ids = {b.id for b in blocks}

    for block_id in block_ids:
        graph[block_id] = []

    for conn in connections:
        if conn.from_block_id in block_ids and conn.to_block_id in block_ids:
            graph[conn.from_block_id].append(conn.to_block_id)

    # BFS от каждого end блока (обратный граф)
    reachable_to_end: Set[int] = set()
    queue = list(end_block_ids)
    reachable_to_end.update(end_block_ids)

    # Строим обратный граф
    reverse_graph: Dict[int, List[int]] = {block_id: [] for block_id in block_ids}
    for from_id, to_ids in graph.items():
        for to_id in to_ids:
            reverse_graph[to_id].append(from_id)

    while queue:
        current = queue.pop(0)
        for predecessor in reverse_graph.get(current, []):
            if predecessor not in reachable_to_end:
                reachable_to_end.add(predecessor)
                queue.append(predecessor)

    # Блоки от которых нельзя добраться до end
    unreachable = block_ids - reachable_to_end
    if unreachable:
        for block_id in unreachable:
            block = next((b for b in blocks if b.id == block_id), None)
            if block and block.block_type != 'end':  # end блоки не должны быть достижимы
                errors.append(
                    f"Block '{block.label}' (id={block_id}, type={block.block_type}) "
                    f"has no path to any 'end' block"
                )

    return errors


def _check_orphaned_blocks(
    blocks: List[FlowBlock],
    connections: List[FlowConnection]
) -> List[str]:
    """
    Проверить orphaned блоки (блоки без входящих соединений)

    Start блоки могут не иметь входящих, остальные должны
    """
    errors = []

    if not blocks:
        return errors

    block_ids = {b.id for b in blocks}

    # Находим блоки с входящими соединениями
    blocks_with_incoming = {conn.to_block_id for conn in connections if conn.to_block_id in block_ids}

    # Блоки без входящих
    orphaned = []
    for block in blocks:
        if block.id not in blocks_with_incoming:
            # Start блоки могут не иметь входящих
            if block.block_type != 'start':
                orphaned.append(block)

    if orphaned:
        for block in orphaned:
            errors.append(
                f"Block '{block.label}' (id={block.id}, type={block.block_type}) "
                f"has no incoming connections"
            )

    return errors


def _validate_block_connections(
    blocks: List[FlowBlock],
    connections: List[FlowConnection]
) -> List[str]:
    """
    Проверить правильность соединений для каждого типа блока

    - end блоки не должны иметь исходящих соединений
    - quiz, decision, confirmation должны иметь 2+ исходящих
    - menu, course_menu должны иметь соединения для каждой кнопки
    """
    errors = []

    if not blocks or not connections:
        return errors

    block_map = {b.id: b for b in blocks}

    # Группируем соединения по from_block_id
    outgoing: Dict[int, List[FlowConnection]] = {}
    for conn in connections:
        if conn.from_block_id not in outgoing:
            outgoing[conn.from_block_id] = []
        outgoing[conn.from_block_id].append(conn)

    for block in blocks:
        block_outgoing = outgoing.get(block.id, [])

        # end блоки не должны иметь исходящих
        if block.block_type == 'end' and block_outgoing:
            errors.append(
                f"End block '{block.label}' (id={block.id}) has {len(block_outgoing)} "
                f"outgoing connections, should have 0"
            )

        # start блоки должны иметь хотя бы 1 исходящее
        elif block.block_type == 'start' and not block_outgoing:
            errors.append(
                f"Start block '{block.label}' (id={block.id}) has no outgoing connections"
            )

        # quiz блоки должны иметь 2 исходящих (correct/wrong)
        elif block.block_type == 'quiz':
            if len(block_outgoing) < 2:
                errors.append(
                    f"Quiz block '{block.label}' (id={block.id}) has {len(block_outgoing)} "
                    f"outgoing connections, should have at least 2 (correct/wrong)"
                )

        # decision блоки должны иметь 2 исходящих (true/false)
        elif block.block_type == 'decision':
            if len(block_outgoing) < 2:
                errors.append(
                    f"Decision block '{block.label}' (id={block.id}) has {len(block_outgoing)} "
                    f"outgoing connections, should have at least 2 (true/false)"
                )

        # confirmation блоки должны иметь 2 исходящих (confirmed/cancelled)
        elif block.block_type == 'confirmation':
            if len(block_outgoing) < 2:
                errors.append(
                    f"Confirmation block '{block.label}' (id={block.id}) has {len(block_outgoing)} "
                    f"outgoing connections, should have at least 2 (confirmed/cancelled)"
                )

        # payment_gate блоки должны иметь 2 исходящих (paid/unpaid)
        elif block.block_type == 'payment_gate':
            if len(block_outgoing) < 2:
                errors.append(
                    f"Payment gate block '{block.label}' (id={block.id}) has {len(block_outgoing)} "
                    f"outgoing connections, should have at least 2 (paid/unpaid)"
                )

    return errors


async def validate_flow_before_activation(
    flow_id: int,
    session: AsyncSession
) -> Tuple[bool, List[str]]:
    """
    Валидировать flow перед активацией

    Returns:
        (is_valid, errors)
    """
    # Загружаем flow
    result = await session.execute(
        select(ConversationFlow).where(ConversationFlow.id == flow_id)
    )
    flow = result.scalar_one_or_none()

    if not flow:
        return False, ["Flow not found"]

    # Загружаем блоки
    blocks_result = await session.execute(
        select(FlowBlock).where(FlowBlock.flow_id == flow_id)
    )
    blocks = blocks_result.scalars().all()

    # Загружаем соединения
    connections_result = await session.execute(
        select(FlowConnection).where(FlowConnection.flow_id == flow_id)
    )
    connections = connections_result.scalars().all()

    return await validate_flow_structure(flow, blocks, connections)
