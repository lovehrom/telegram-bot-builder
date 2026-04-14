"""Add conversation flow tables

Revision ID: 001_add_flow_tables
Revises:
Create Date: 2025-02-02 18:41:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_flow_tables'
down_revision: Union[str, None] = '000_initial_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create flow_blocks table FIRST (before conversation_flows)
    op.create_table(
        'flow_blocks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('flow_id', sa.Integer(), nullable=True),  # Make nullable initially
        sa.Column('block_type', sa.String(length=50), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('position_x', sa.Integer(), nullable=True),
        sa.Column('position_y', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name='pk_flow_blocks')
    )
    # Foreign key will be added after conversation_flows is created

    # Create conversation_flows table SECOND
    op.create_table(
        'conversation_flows',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('start_block_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['start_block_id'], ['flow_blocks.id'], name='fk_conversation_flows_start_block'),
        sa.PrimaryKeyConstraint('id', name='pk_conversation_flows')
    )

    # Foreign key will be added later via separate migration
    # For now, just create the index
    op.create_index('ix_flow_blocks_flow_id', 'flow_blocks', ['flow_id'])

    # Create flow_connections table
    op.create_table(
        'flow_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('flow_id', sa.Integer(), nullable=False),
        sa.Column('from_block_id', sa.Integer(), nullable=False),
        sa.Column('to_block_id', sa.Integer(), nullable=False),
        sa.Column('condition', sa.String(length=255), nullable=True),
        sa.Column('condition_config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('connection_style', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['flow_id'], ['conversation_flows.id'], name='fk_flow_connections_flow', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_block_id'], ['flow_blocks.id'], name='fk_flow_connections_from_block', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_block_id'], ['flow_blocks.id'], name='fk_flow_connections_to_block', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_flow_connections'),
        sa.UniqueConstraint('from_block_id', 'condition', name='uq_block_condition')
    )
    op.create_index('ix_flow_connections_flow_id', 'flow_connections', ['flow_id'])
    op.create_index('ix_flow_connections_from_block_id', 'flow_connections', ['from_block_id'])
    op.create_index('ix_flow_connections_to_block_id', 'flow_connections', ['to_block_id'])

    # Create user_flow_states table
    op.create_table(
        'user_flow_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('flow_id', sa.Integer(), nullable=False),
        sa.Column('current_block_id', sa.Integer(), nullable=True),
        sa.Column('context', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_flow_states_user', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['flow_id'], ['conversation_flows.id'], name='fk_user_flow_states_flow', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['current_block_id'], ['flow_blocks.id'], name='fk_user_flow_states_current_block'),
        sa.PrimaryKeyConstraint('id', name='pk_user_flow_states'),
        sa.UniqueConstraint('user_id', 'flow_id', name='uq_user_flow')
    )
    op.create_index('ix_user_flow_states_user_id', 'user_flow_states', ['user_id'])
    op.create_index('ix_user_flow_states_flow_id', 'user_flow_states', ['flow_id'])


def downgrade() -> None:
    op.drop_index('ix_user_flow_states_flow_id', table_name='user_flow_states')
    op.drop_index('ix_user_flow_states_user_id', table_name='user_flow_states')
    op.drop_table('user_flow_states')

    op.drop_index('ix_flow_connections_to_block_id', table_name='flow_connections')
    op.drop_index('ix_flow_connections_from_block_id', table_name='flow_connections')
    op.drop_index('ix_flow_connections_flow_id', table_name='flow_connections')
    op.drop_table('flow_connections')

    op.drop_index('ix_flow_blocks_flow_id', table_name='flow_blocks')
    op.drop_table('flow_blocks')

    op.drop_table('conversation_flows')
