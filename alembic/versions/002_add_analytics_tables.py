"""add analytics tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create api_analytics table
    op.create_table(
        'api_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('response_time', sa.Float(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('success', sa.Integer(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['api_id'], ['api.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_api_analytics_api_timestamp',
        'api_analytics',
        ['api_id', 'timestamp']
    )
    op.create_index(
        'ix_api_analytics_timestamp',
        'api_analytics',
        ['timestamp']
    )

    # Create api_trend table
    op.create_table(
        'api_trend',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('period', sa.Integer(), nullable=False),
        sa.Column('avg_response_time', sa.Float(), nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=False),
        sa.Column('error_rate', sa.Float(), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['api_id'], ['api.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_api_trend_api_timestamp',
        'api_trend',
        ['api_id', 'timestamp']
    )
    op.create_index(
        'ix_api_trend_timestamp',
        'api_trend',
        ['timestamp']
    )


def downgrade():
    # Drop api_trend table and its indexes
    op.drop_index('ix_api_trend_timestamp', table_name='api_trend')
    op.drop_index('ix_api_trend_api_timestamp', table_name='api_trend')
    op.drop_table('api_trend')

    # Drop api_analytics table and its indexes
    op.drop_index('ix_api_analytics_timestamp', table_name='api_analytics')
    op.drop_index('ix_api_analytics_api_timestamp', table_name='api_analytics')
    op.drop_table('api_analytics') 