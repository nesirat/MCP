"""add notification tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create notification_config table
    op.create_table(
        'notification_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_notification_config_user_id',
        'notification_config',
        ['user_id']
    )

    # Create notification_log table
    op.create_table(
        'notification_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_config_id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['notification_config_id'], ['notification_config.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['alert_id'], ['alert.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_notification_log_notification_config_id',
        'notification_log',
        ['notification_config_id']
    )
    op.create_index(
        'ix_notification_log_alert_id',
        'notification_log',
        ['alert_id']
    )
    op.create_index(
        'ix_notification_log_created_at',
        'notification_log',
        ['created_at']
    )

def downgrade():
    # Drop notification_log table
    op.drop_index('ix_notification_log_created_at', table_name='notification_log')
    op.drop_index('ix_notification_log_alert_id', table_name='notification_log')
    op.drop_index('ix_notification_log_notification_config_id', table_name='notification_log')
    op.drop_table('notification_log')

    # Drop notification_config table
    op.drop_index('ix_notification_config_user_id', table_name='notification_config')
    op.drop_table('notification_config') 