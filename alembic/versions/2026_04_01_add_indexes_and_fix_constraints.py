"""Add index on FlowConnection.from_block_id, fix constraint name, add UserFlowState indexes

Revision ID: 2026_04_01_add_indexes_and_fix_constraints
Revises: 2026_03_31_fix_flow_conn_constraint
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2026_04_01_add_indexes_and_fix_constraints'
down_revision = '2026_03_31_fix_flow_conn_constraint'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавить индексы и исправить имена constraint"""
    # 1. Переименовать constraint к имени из модели (uq_block_to_condition)
    op.drop_constraint('uq_flow_conn_block_to_condition', 'flow_connections', type_='unique')
    op.create_unique_constraint(
        'uq_block_to_condition',
        'flow_connections',
        ['from_block_id', 'to_block_id', 'condition']
    )

    # 2. Индекс на FlowConnection.from_block_id (если ещё нет)
    # Проверяем существование через try/except — Alembic не имеет if_exists для индексов
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('flow_connections')]
    if 'ix_flow_connections_from_block_id' not in existing_indexes:
        op.create_index('ix_flow_connections_from_block_id', 'flow_connections', ['from_block_id'])

    # 3. Индексы на UserFlowState
    user_flow_existing = [idx['name'] for idx in inspector.get_indexes('user_flow_states')]
    if 'ix_user_flow_state_user_completed' not in user_flow_existing:
        op.create_index('ix_user_flow_state_user_completed', 'user_flow_states', ['user_id', 'is_completed'])
    if 'ix_user_flow_state_flow_id' not in user_flow_existing:
        op.create_index('ix_user_flow_state_flow_id', 'user_flow_states', ['flow_id'])


def downgrade() -> None:
    """Откат изменений"""
    # Удалить индексы UserFlowState
    op.drop_index('ix_user_flow_state_flow_id', table_name='user_flow_states')
    op.drop_index('ix_user_flow_state_user_completed', table_name='user_flow_states')

    # Удалить индекс FlowConnection
    op.drop_index('ix_flow_connections_from_block_id', table_name='flow_connections')

    # Вернуть старое имя constraint
    op.drop_constraint('uq_block_to_condition', 'flow_connections', type_='unique')
    op.create_unique_constraint(
        'uq_flow_conn_block_to_condition',
        'flow_connections',
        ['from_block_id', 'to_block_id', 'condition']
    )
