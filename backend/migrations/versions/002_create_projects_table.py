"""create projects table

Revision ID: 002
Revises: 001
Create Date: 2025-11-10 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 projects 表 - 文档管理和项目核心功能
    op.create_table('projects',
        sa.Column('id', sa.String(), nullable=False, comment='主键ID'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='项目标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='项目描述'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='项目状态'),
        sa.Column('user_id', sa.String(), nullable=False, comment='所有者用户ID'),
        sa.Column('original_filename', sa.String(length=255), nullable=True, comment='原始文件名'),
        sa.Column('file_path', sa.String(length=500), nullable=True, comment='文件存储路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        sa.Column('file_type', sa.String(length=10), nullable=True, comment='文件类型'),
        sa.Column('file_hash', sa.String(length=64), nullable=True, comment='文件哈希值（SHA-256）'),
        sa.Column('file_processing_status', sa.String(length=20), nullable=False, comment='文件处理状态'),
        sa.Column('total_chapters', sa.Integer(), nullable=False, comment='章节数量'),
        sa.Column('total_paragraphs', sa.Integer(), nullable=False, comment='段落数量'),
        sa.Column('total_sentences', sa.Integer(), nullable=False, comment='句子数量'),
        sa.Column('word_count', sa.Integer(), nullable=False, comment='字数统计'),
        sa.Column('processing_config', sa.JSON(), nullable=True, comment='处理配置（JSON格式）'),
        sa.Column('minio_bucket', sa.String(length=100), nullable=True, comment='MinIO存储桶'),
        sa.Column('minio_object_key', sa.String(length=500), nullable=True, comment='MinIO对象键'),
        sa.Column('processing_error', sa.Text(), nullable=True, comment='处理错误信息'),
        sa.Column('processing_progress', sa.Float(), nullable=False, comment='处理进度（0-100）'),
        sa.Column('is_public', sa.Boolean(), nullable=False, comment='是否公开'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='是否已删除'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_projects_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_project_user_status', 'user_id', 'status', 'is_deleted'),
        sa.Index('idx_project_file_status', 'file_processing_status', 'created_at'),
        sa.Index('idx_project_title_search', 'title'),
        comment='项目表'
    )

    # 为 projects 表创建更新时间触发器
    op.execute("""
        CREATE TRIGGER update_projects_updated_at
            BEFORE UPDATE ON projects
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    # 删除触发器
    op.execute("DROP TRIGGER IF EXISTS update_projects_updated_at ON projects")

    # 删除表
    op.drop_table('projects')