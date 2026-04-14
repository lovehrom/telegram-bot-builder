"""Add is_global_menu field to conversation_flows

Revision ID: 005_add_is_global_menu
Revises: 004_add_flow_templates
Create Date: 2026-02-05 16:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_is_global_menu'
down_revision: Union[str, None] = '004_add_flow_templates'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавить поле is_global_menu в conversation_flows
    op.add_column(
        'conversation_flows',
        sa.Column('is_global_menu', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    # Удалить поле is_global_menu
    op.drop_column('conversation_flows', 'is_global_menu')
