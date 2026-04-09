"""add commission sample numbering tables

Revision ID: cfc057acdbbc
Revises: 007840f1a79e
Create Date: 2026-04-08 20:22:05.834992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cfc057acdbbc'
down_revision: Union[str, None] = '007840f1a79e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('numbering_rules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('prefix', sa.String(length=20), nullable=False),
    sa.Column('date_format', sa.String(length=20), nullable=True),
    sa.Column('separator', sa.String(length=5), nullable=True),
    sa.Column('sequence_digits', sa.Integer(), nullable=True),
    sa.Column('sequence_reset', sa.String(length=20), nullable=True),
    sa.Column('current_sequence', sa.Integer(), nullable=True),
    sa.Column('last_reset_date', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_numbering_rules_entity_type'), 'numbering_rules', ['entity_type'], unique=True)
    op.create_index(op.f('ix_numbering_rules_id'), 'numbering_rules', ['id'], unique=False)
    op.create_table('commissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('commission_no', sa.String(length=50), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('sub_item_id', sa.Integer(), nullable=False),
    sa.Column('client_name', sa.String(length=100), nullable=False),
    sa.Column('client_contact', sa.String(length=50), nullable=True),
    sa.Column('client_phone', sa.String(length=20), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('sample_count', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('submitted_by', sa.Integer(), nullable=False),
    sa.Column('reviewed_by', sa.Integer(), nullable=True),
    sa.Column('review_comment', sa.Text(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['sub_item_id'], ['sub_items.id'], ),
    sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_commissions_commission_no'), 'commissions', ['commission_no'], unique=True)
    op.create_index(op.f('ix_commissions_id'), 'commissions', ['id'], unique=False)
    op.create_table('samples',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sample_no', sa.String(length=50), nullable=False),
    sa.Column('commission_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('material_type', sa.String(length=50), nullable=True),
    sa.Column('specification', sa.String(length=100), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('quantity_unit', sa.String(length=20), nullable=True),
    sa.Column('sampling_date', sa.Date(), nullable=True),
    sa.Column('sampling_location', sa.String(length=200), nullable=True),
    sa.Column('sampler', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('received_by', sa.Integer(), nullable=True),
    sa.Column('received_at', sa.DateTime(), nullable=True),
    sa.Column('storage_location', sa.String(length=100), nullable=True),
    sa.Column('retention_deadline', sa.Date(), nullable=True),
    sa.Column('disposed_at', sa.DateTime(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['commission_id'], ['commissions.id'], ),
    sa.ForeignKeyConstraint(['received_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_samples_id'), 'samples', ['id'], unique=False)
    op.create_index(op.f('ix_samples_sample_no'), 'samples', ['sample_no'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_samples_sample_no'), table_name='samples')
    op.drop_index(op.f('ix_samples_id'), table_name='samples')
    op.drop_table('samples')
    op.drop_index(op.f('ix_commissions_commission_no'), table_name='commissions')
    op.drop_index(op.f('ix_commissions_id'), table_name='commissions')
    op.drop_table('commissions')
    op.drop_index(op.f('ix_numbering_rules_entity_type'), table_name='numbering_rules')
    op.drop_index(op.f('ix_numbering_rules_id'), table_name='numbering_rules')
    op.drop_table('numbering_rules')
