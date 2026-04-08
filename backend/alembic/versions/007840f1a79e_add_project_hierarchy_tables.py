"""add project hierarchy tables

Revision ID: 007840f1a79e
Revises: 8a43dbdaf2de
Create Date: 2026-04-08 02:17:00.509824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007840f1a79e'
down_revision: Union[str, None] = '8a43dbdaf2de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('location', sa.String(length=200), nullable=True),
    sa.Column('client_name', sa.String(length=100), nullable=True),
    sa.Column('contact_person', sa.String(length=50), nullable=True),
    sa.Column('contact_phone', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_code'), 'projects', ['code'], unique=True)
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_table('unit_projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unit_projects_code'), 'unit_projects', ['code'], unique=False)
    op.create_index(op.f('ix_unit_projects_id'), 'unit_projects', ['id'], unique=False)
    op.create_table('divisions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('unit_project_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['unit_project_id'], ['unit_projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_divisions_code'), 'divisions', ['code'], unique=False)
    op.create_index(op.f('ix_divisions_id'), 'divisions', ['id'], unique=False)
    op.create_table('sub_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('division_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['division_id'], ['divisions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sub_items_code'), 'sub_items', ['code'], unique=False)
    op.create_index(op.f('ix_sub_items_id'), 'sub_items', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sub_items_id'), table_name='sub_items')
    op.drop_index(op.f('ix_sub_items_code'), table_name='sub_items')
    op.drop_table('sub_items')
    op.drop_index(op.f('ix_divisions_id'), table_name='divisions')
    op.drop_index(op.f('ix_divisions_code'), table_name='divisions')
    op.drop_table('divisions')
    op.drop_index(op.f('ix_unit_projects_id'), table_name='unit_projects')
    op.drop_index(op.f('ix_unit_projects_code'), table_name='unit_projects')
    op.drop_table('unit_projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_code'), table_name='projects')
    op.drop_table('projects')
