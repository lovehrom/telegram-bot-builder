"""Create FlowProgress model and migrate UserProgress

Revision ID: 2026_03_22_flow_progress
Revises: 005_add_is_global_menu
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026_03_22_flow_progress'
down_revision = '005_add_is_global_menu'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create flow_progress table and migrate data from user_progress"""

    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Пропустить если таблица уже существует (ручное создание или предыдущий запуск)
    if 'flow_progress' not in inspector.get_table_names():
        # Create flow_progress table
        op.create_table(
            'flow_progress',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('flow_id', sa.Integer(), nullable=False),
            sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
            sa.Column('correct_answers', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_questions', sa.Integer(), server_default='0', nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('passed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('metadata', postgresql.JSON(), nullable=False, server_default='{}'),
            sa.ForeignKeyConstraint(['flow_id'], ['conversation_flows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id', 'flow_id', name='uq_user_flow_progress')
        )

        # Indexes
        op.create_index('ix_flow_progress_user_id', 'flow_progress', ['user_id'])
        op.create_index('ix_flow_progress_flow_id', 'flow_progress', ['flow_id'])

    # Drop old tables if they exist (from previous schema)
    for table_name in ['user_progress', 'questions', 'lessons']:
        try:
            conn.execute(sa.text(f'DROP TABLE IF EXISTS {table_name} CASCADE'))
            conn.commit()
        except Exception:
            conn.rollback()
            pass


def downgrade() -> None:
    """Drop flow_progress table - can't easily restore without data loss"""
    op.drop_index('ix_flow_progress_flow_id', table_name='flow_progress')
    op.drop_index('ix_flow_progress_user_id', table_name='flow_progress')
    op.drop_table('flow_progress')
