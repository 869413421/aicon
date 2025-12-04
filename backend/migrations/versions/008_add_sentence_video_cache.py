"""添加句子视频缓存字段

Revision ID: 008
Revises: 007
Create Date: 2024-12-04 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    """添加句子视频缓存相关字段"""
    # 添加视频缓存字段
    op.add_column('sentences', sa.Column('sentence_video_key', sa.String(500), nullable=True, comment='单句视频MinIO对象键'))
    op.add_column('sentences', sa.Column('sentence_video_duration', sa.Integer, nullable=True, comment='单句视频时长（秒）'))
    op.add_column('sentences', sa.Column('needs_regeneration', sa.Boolean, server_default='true', nullable=False, comment='是否需要重新生成视频'))
    op.add_column('sentences', sa.Column('last_video_generated_at', sa.DateTime, nullable=True, comment='最后生成视频时间'))
    
    # 创建索引以优化查询
    op.create_index('idx_sentence_needs_regen', 'sentences', ['needs_regeneration'])


def downgrade():
    """回滚：删除句子视频缓存字段"""
    # 删除索引
    op.drop_index('idx_sentence_needs_regen', table_name='sentences')
    
    # 删除字段
    op.drop_column('sentences', 'last_video_generated_at')
    op.drop_column('sentences', 'needs_regeneration')
    op.drop_column('sentences', 'sentence_video_duration')
    op.drop_column('sentences', 'sentence_video_key')
