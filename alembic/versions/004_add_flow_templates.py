"""Add flow templates table

Revision ID: 004_add_flow_templates
Revises: 003_add_media_library
Create Date: 2026-02-03 21:50:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = '004_add_flow_templates'
down_revision: Union[str, None] = '003_add_media_library'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создать таблицу flow_templates
    op.create_table(
        'flow_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('blocks_data', JSON(), nullable=False),
        sa.Column('connections_data', JSON(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_flow_templates')
    )


def downgrade() -> None:
    # Удалить таблицу flow_templates
    op.drop_table('flow_templates')
