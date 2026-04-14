"""Fix FlowConnection unique constraint: from_block_id+condition -> from_block_id+to_block_id+condition

Revision ID: 2026_03_31_fix_flow_conn_constraint
Revises: 2026_03_22_flow_progress
Create Date: 2026-03-31

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '2026_03_31_fix_flow_conn_constraint'
down_revision = '2026_03_22_flow_progress'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Заменить уникальный constraint с (from_block_id, condition) на (from_block_id, to_block_id, condition)"""
    # Удалить старый constraint
    op.drop_constraint('uq_block_condition', 'flow_connections', type_='unique')
    # Создать новый — учитывает to_block_id, чтобы одинаковые условия могли вести к разным блокам
    op.create_unique_constraint(
        'uq_flow_conn_block_to_condition',
        'flow_connections',
        ['from_block_id', 'to_block_id', 'condition']
    )


def downgrade() -> None:
    """Откат к старому constraint"""
    op.drop_constraint('uq_flow_conn_block_to_condition', 'flow_connections', type_='unique')
    op.create_unique_constraint('uq_block_condition', 'flow_connections', ['from_block_id', 'condition'])
