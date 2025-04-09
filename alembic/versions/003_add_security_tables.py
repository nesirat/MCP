"""add security tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_action', 'audit_log', ['action'])
    op.create_index(
        'ix_audit_log_resource',
        'audit_log',
        ['resource_type', 'resource_id']
    )
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])

    # Create rate_limit table
    op.create_table(
        'rate_limit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('window_start', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_rate_limit_user_endpoint',
        'rate_limit',
        ['user_id', 'endpoint']
    )
    op.create_index(
        'ix_rate_limit_window_start',
        'rate_limit',
        ['window_start']
    )


def downgrade():
    # Drop rate_limit table and its indexes
    op.drop_index('ix_rate_limit_window_start', table_name='rate_limit')
    op.drop_index('ix_rate_limit_user_endpoint', table_name='rate_limit')
    op.drop_table('rate_limit')

    # Drop audit_log table and its indexes
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_index('ix_audit_log_resource', table_name='audit_log')
    op.drop_index('ix_audit_log_action', table_name='audit_log')
    op.drop_index('ix_audit_log_user_id', table_name='audit_log')
    op.drop_table('audit_log') 