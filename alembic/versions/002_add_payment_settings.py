"""Add payment settings table

Revision ID: 002_add_payment_settings
Revises: 001_add_flow_tables
Create Date: 2026-02-03 17:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_payment_settings'
down_revision: Union[str, None] = '001_add_flow_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payment_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_provider_token', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('is_test_mode', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('payment_title', sa.String(length=255), nullable=False, server_default='Доступ к курсу'),
        sa.Column('payment_description', sa.String(length=500), nullable=False, server_default='Полный доступ ко всем урокам'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='RUB'),
        sa.Column('price_amount', sa.Integer(), nullable=False, server_default='9900'),
        sa.PrimaryKeyConstraint('id', name='pk_payment_settings')
    )

    # Создать первую запись с id=1
    op.execute("INSERT INTO payment_settings (id, payment_provider_token, is_test_mode, payment_title, payment_description, currency, price_amount) VALUES (1, '', true, 'Доступ к курсу', 'Полный доступ ко всем урокам', 'RUB', 9900)")


def downgrade() -> None:
    op.drop_table('payment_settings')
