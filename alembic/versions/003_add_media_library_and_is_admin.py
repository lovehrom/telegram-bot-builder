"""Add media library table and is_admin field to users

Revision ID: 003_add_media_library
Revises: 002_add_payment_settings
Create Date: 2026-02-03 21:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_media_library'
down_revision: Union[str, None] = '002_add_payment_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Поле is_admin уже добавлено в миграции 000_initial_tables
    # Создаем только таблицу media_library
    op.create_table(
        'media_library',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('file_id', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('uploaded_by', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id', name='pk_media_library')
    )


def downgrade() -> None:
    # Удалить таблицу media_library
    # Поле is_admin будет удалено при откате миграции 000_initial_tables
    op.drop_table('media_library')
