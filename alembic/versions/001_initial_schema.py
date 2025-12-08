"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-12-08

Creates tables for:
- graphs: Workflow definitions
- runs: Workflow execution instances
- execution_logs: Node execution history
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema"""

    # Determine JSON type based on database dialect
    bind = op.get_bind()
    json_type = JSONB if bind.dialect.name == 'postgresql' else JSON

    # Create graphs table
    op.create_table(
        'graphs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('definition', json_type, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_graphs_name', 'graphs', ['name'])

    # Create runs table
    op.create_table(
        'runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=255), nullable=False),
        sa.Column('graph_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='executionstatus'), nullable=False),
        sa.Column('initial_state', json_type, nullable=False),
        sa.Column('final_state', json_type, nullable=True),
        sa.Column('current_state', json_type, nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_execution_time_ms', sa.Float(), nullable=True),
        sa.Column('total_iterations', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['graph_id'], ['graphs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id')
    )
    op.create_index('ix_runs_run_id', 'runs', ['run_id'])
    op.create_index('ix_runs_graph_id', 'runs', ['graph_id'])
    op.create_index('ix_runs_status', 'runs', ['status'])
    op.create_index('idx_run_status_created', 'runs', ['status', 'created_at'])
    op.create_index('idx_run_graph_status', 'runs', ['graph_id', 'status'])

    # Create execution_logs table
    op.create_table(
        'execution_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('node_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('STARTED', 'COMPLETED', 'FAILED', name='nodeexecutionstatus'), nullable=False),
        sa.Column('iteration', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('state_snapshot', json_type, nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_execution_logs_run_id', 'execution_logs', ['run_id'])
    op.create_index('ix_execution_logs_node_name', 'execution_logs', ['node_name'])
    op.create_index('ix_execution_logs_status', 'execution_logs', ['status'])
    op.create_index('ix_execution_logs_timestamp', 'execution_logs', ['timestamp'])
    op.create_index('idx_log_run_timestamp', 'execution_logs', ['run_id', 'timestamp'])
    op.create_index('idx_log_run_node', 'execution_logs', ['run_id', 'node_name'])


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('execution_logs')
    op.drop_table('runs')
    op.drop_table('graphs')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS nodeexecutionstatus')
    op.execute('DROP TYPE IF EXISTS executionstatus')
