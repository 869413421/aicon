"""add shot field to movie_shots

Revision ID: 022
Revises: 021
Create Date: 2025-12-24 19:03:00.000000

Changes:
1. Add shot field to movie_shots
2. Migrate data from visual_description to shot
3. Drop visual_description and camera_movement fields
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add shot column
    op.add_column('movie_shots', sa.Column('shot', sa.Text(), nullable=True))
    
    # 2. Migrate data: copy visual_description to shot
    op.execute("UPDATE movie_shots SET shot = visual_description WHERE visual_description IS NOT NULL")
    
    # 3. Make shot NOT NULL after migration
    op.alter_column('movie_shots', 'shot', nullable=False)
    
    # 4. Drop old columns
    op.drop_column('movie_shots', 'visual_description')
    op.drop_column('movie_shots', 'camera_movement')


def downgrade():
    # WARNING: This downgrade will lose data!
    
    # 1. Restore old columns
    op.add_column('movie_shots', sa.Column('visual_description', sa.Text(), nullable=True))
    op.add_column('movie_shots', sa.Column('camera_movement', sa.String(length=200), nullable=True))
    
    # 2. Restore data from shot to visual_description
    op.execute("UPDATE movie_shots SET visual_description = shot WHERE shot IS NOT NULL")
    
    # 3. Make visual_description NOT NULL
    op.alter_column('movie_shots', 'visual_description', nullable=False)
    
    # 4. Drop shot column
    op.drop_column('movie_shots', 'shot')
