"""create bilibili publish tables

Revision ID: 009_create_bilibili_tables
Revises: 008_add_sentence_video_cache
Create Date: 2025-12-11 13:14:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_create_bilibili_tables'
down_revision = '008_add_sentence_video_cache'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 bilibili_accounts 表
    op.create_table(
        'bilibili_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=False, comment='账号名称'),
        sa.Column('cookie_path', sa.String(length=500), nullable=True, comment='cookie.json存储路径'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='最后登录时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bilibili_account_user', 'bilibili_accounts', ['user_id'], unique=False)

    # 创建 publish_tasks 表
    op.create_table(
        'publish_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False, comment='章节外键'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='用户ID'),
        sa.Column('platform', sa.String(length=20), nullable=True, comment='发布平台'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='视频标题'),
        sa.Column('desc', sa.Text(), nullable=True, comment='视频简介'),
        sa.Column('cover_url', sa.String(length=500), nullable=True, comment='封面URL'),
        sa.Column('tid', sa.Integer(), nullable=True, comment='B站分区ID'),
        sa.Column('tag', sa.String(length=500), nullable=True, comment='标签,逗号分隔'),
        sa.Column('copyright', sa.Integer(), nullable=True, comment='1原创 2转载'),
        sa.Column('source', sa.String(length=200), nullable=True, comment='转载来源'),
        sa.Column('dynamic', sa.String(length=500), nullable=True, comment='空间动态'),
        sa.Column('dtime', sa.Integer(), nullable=True, comment='延时发布时间戳'),
        sa.Column('upload_line', sa.String(length=20), nullable=True, comment='上传线路'),
        sa.Column('upload_limit', sa.Integer(), nullable=True, comment='并发数'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='发布状态'),
        sa.Column('bvid', sa.String(length=50), nullable=True, comment='B站BV号'),
        sa.Column('aid', sa.String(length=50), nullable=True, comment='B站AV号'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('progress', sa.Integer(), nullable=True, comment='上传进度 0-100'),
        sa.Column('celery_task_id', sa.String(length=100), nullable=True, comment='Celery任务ID'),
        sa.Column('published_at', sa.DateTime(), nullable=True, comment='发布完成时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_publish_task_chapter', 'publish_tasks', ['chapter_id'], unique=False)
    op.create_index('idx_publish_task_user', 'publish_tasks', ['user_id'], unique=False)
    op.create_index('idx_publish_task_status', 'publish_tasks', ['status'], unique=False)
    op.create_index('idx_publish_task_platform', 'publish_tasks', ['platform'], unique=False)


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_publish_task_platform', table_name='publish_tasks')
    op.drop_index('idx_publish_task_status', table_name='publish_tasks')
    op.drop_index('idx_publish_task_user', table_name='publish_tasks')
    op.drop_index('idx_publish_task_chapter', table_name='publish_tasks')
    op.drop_index('idx_bilibili_account_user', table_name='bilibili_accounts')
    
    # 删除表
    op.drop_table('publish_tasks')
    op.drop_table('bilibili_accounts')
