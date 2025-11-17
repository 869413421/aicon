# AICG内容分发平台 - 后端服务 Makefile
# 提供开发环境的快速启动和常用命令

.PHONY: help start migrate setup worker beat test lint clean format check install

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
GRAY := \033[90m
RESET := \033[0m

# 项目配置
PROJECT_NAME := aicg-platform-backend
PYTHON := python3
UV := uv
PORT := 8000
HOST := 0.0.0.0

help: ## 显示帮助信息
	@echo "$(BLUE)AICG平台后端服务 - 开发命令集合$(RESET)"
	@echo ""
	@echo "$(GREEN)核心命令:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-12s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo ""
	@echo "$(GREEN)示例:$(RESET)"
	@echo "  make setup     # 初始化开发环境"
	@echo "  make start     # 启动开发服务器"
	@echo "  make migrate   # 运行数据库迁移"

setup: ## 初始化开发环境 (安装依赖 + 数据库迁移)
	@echo "$(BLUE)🚀 初始化开发环境...$(RESET)"
	$(UV) sync
	@echo "$(GREEN)✅ 依赖安装完成$(RESET)"
	$(MAKE) migrate
	@echo "$(GREEN)🎉 开发环境初始化完成!$(RESET)"
	@echo ""
	@echo "$(YELLOW)现在可以运行以下命令启动服务:$(RESET)"
	@echo "  make start"

start: ## 启动开发服务器 (热重载)
	@echo "$(BLUE)🚀 启动开发服务器...$(RESET)"
	@echo "$(GREEN)📍 服务地址: http://$(HOST):$(PORT)$(RESET)"
	@echo "$(GREEN)📖 API文档: http://$(HOST):$(PORT)/docs$(RESET)"
	@echo "$(YELLOW)⚠️  确保先启动基础设施服务: cd .. && ./scripts/start.sh$(RESET)"
	@echo ""
	$(UV) run uvicorn src.main:app --reload --host $(HOST) --port $(PORT)

migrate: ## 运行数据库迁移
	@echo "$(BLUE)🔄 运行数据库迁移...$(RESET)"
	$(UV) run alembic upgrade head
	@echo "$(GREEN)✅ 数据库迁移完成$(RESET)"


migrate-down: ## 回滚最后一次数据库迁移
	@echo "$(YELLOW)⚠️  回滚数据库迁移...$(RESET)"
	$(UV) run alembic downgrade -1
	@echo "$(GREEN)✅ 迁移回滚完成$(RESET)"

worker: ## 启动Celery Worker
	@echo "$(BLUE)🔄 启动Celery Worker...$(RESET)"
	$(UV) run celery -A src.tasks.file_processing worker --loglevel=info --concurrency=4

beat: ## 启动Celery Beat (定时任务调度器)
	@echo "$(BLUE)⏰ 启动Celery Beat...$(RESET)"
	$(UV) run celery -A src.workers.base beat --loglevel=info

test: ## 运行所有测试
	@echo "$(BLUE)🧪 运行测试...$(RESET)"
	$(UV) run pytest
	@echo "$(GREEN)✅ 测试完成$(RESET)"

clean: ## 清理临时文件和缓存
	@echo "$(BLUE)🧹 清理项目...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage coverage.xml
	@echo "$(GREEN)✅ 清理完成$(RESET)"

install: ## 安装开发依赖
	@echo "$(BLUE)📦 安装开发依赖...$(RESET)"
	$(UV) sync --dev
	@echo "$(GREEN)✅ 依赖安装完成$(RESET)"

shell: ## 启动Python Shell (带项目环境)
	@echo "$(BLUE)🐍 启动Python Shell...$(RESET)"
	$(UV) run python

db-status: ## 查看数据库迁移状态
	@echo "$(BLUE)📊 数据库迁移状态:$(RESET)"
	$(UV) run alembic current
