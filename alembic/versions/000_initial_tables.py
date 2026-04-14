"""Initial tables creation

Revision ID: 000_initial_tables
Revises:
Create Date: 2025-02-04 13:35:00

"""
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '000_initial_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('registration_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('current_lesson_number', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id', name='pk_users')
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_index('ix_users_is_paid', 'users', ['is_paid'])

    # Create lessons table
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('video_file_id', sa.String(length=255), nullable=True),
        sa.Column('is_free', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id', name='pk_lessons'),
        sa.UniqueConstraint('order_number', name='uq_lesson_order')
    )
    op.create_index('ix_lessons_order_number', 'lessons', ['order_number'], unique=True)

    # Create questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(length=500), nullable=False),
        sa.Column('options', postgresql.JSON(), nullable=False),
        sa.Column('correct_option_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name='fk_questions_lesson', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_questions')
    )
    op.create_index('ix_questions_lesson_id', 'questions', ['lesson_id'])

    # Create user_progress table
    op.create_table(
        'user_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('correct_answers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_progress_user', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name='fk_user_progress_lesson', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_user_progress'),
        sa.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson')
    )
    op.create_index('ix_user_progress_user_id', 'user_progress', ['user_id'])
    op.create_index('ix_user_progress_lesson_id', 'user_progress', ['lesson_id'])
    op.create_index('ix_user_progress_completed_at', 'user_progress', ['completed_at'])


def downgrade() -> None:
    op.drop_index('ix_user_progress_completed_at', table_name='user_progress')
    op.drop_index('ix_user_progress_lesson_id', table_name='user_progress')
    op.drop_index('ix_user_progress_user_id', table_name='user_progress')
    op.drop_table('user_progress')

    op.drop_index('ix_questions_lesson_id', table_name='questions')
    op.drop_table('questions')

    op.drop_index('ix_lessons_order_number', table_name='lessons')
    op.drop_table('lessons')

    op.drop_index('ix_users_is_paid', table_name='users')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_table('users')
