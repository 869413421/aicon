"""add generation history table

Revision ID: 027_add_generation_history_table
Revises: 026_add_video_task_type
Create Date: 2025-12-29 11:08:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 movie_generation_history 表
    op.create_table(
        'movie_generation_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        
        # 资源类型和ID
        sa.Column('resource_type', sa.String(length=50), nullable=False, comment='资源类型: scene_image/shot_keyframe/character_avatar/transition_video'),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False, comment='资源ID（scene_id/shot_id/character_id/transition_id）'),
        
        # 媒体类型
        sa.Column('media_type', sa.String(length=20), nullable=False, comment='媒体类型: image/video'),
        
        # 生成结果
        sa.Column('result_url', sa.String(length=500), nullable=False, comment='生成的图片/视频URL'),
        sa.Column('prompt', sa.Text(), nullable=False, comment='生成时使用的提示词'),
        
        # 生成参数
        sa.Column('model', sa.String(length=100), nullable=True, comment='使用的模型名称'),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=True, comment='使用的API Key'),
        
        # 选择状态
        sa.Column('is_selected', sa.Boolean(), nullable=True, server_default='false', comment='是否被选中使用'),
        
        # 主键
        sa.PrimaryKeyConstraint('id'),
        
        # 外键
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ),
        
        # 索引
        sa.Index('idx_resource_type_id', 'resource_type', 'resource_id'),
        sa.Index('idx_resource_selected', 'resource_type', 'resource_id', 'is_selected'),
    )
    
    # 创建单独的索引
    op.create_index('ix_movie_generation_history_resource_type', 'movie_generation_history', ['resource_type'])
    op.create_index('ix_movie_generation_history_resource_id', 'movie_generation_history', ['resource_id'])
    op.create_index('ix_movie_generation_history_media_type', 'movie_generation_history', ['media_type'])
    op.create_index('ix_movie_generation_history_is_selected', 'movie_generation_history', ['is_selected'])
    op.create_index('ix_movie_generation_history_api_key_id', 'movie_generation_history', ['api_key_id'])


def downgrade():
    # 删除索引
    op.drop_index('ix_movie_generation_history_api_key_id', table_name='movie_generation_history')
    op.drop_index('ix_movie_generation_history_is_selected', table_name='movie_generation_history')
    op.drop_index('ix_movie_generation_history_media_type', table_name='movie_generation_history')
    op.drop_index('ix_movie_generation_history_resource_id', table_name='movie_generation_history')
    op.drop_index('ix_movie_generation_history_resource_type', table_name='movie_generation_history')
    
    # 删除表
    op.drop_table('movie_generation_history')
