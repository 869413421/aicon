# Docker 镜像构建和推送脚本 (Windows PowerShell)
# 用法: .\build-and-push.ps1 [-Version "v1.0.0"]

param(
    [string]$Version = "latest"
)

$ErrorActionPreference = "Stop"

$REGISTRY = "docker.io"
$USERNAME = "qingshui869413421"

Write-Host "🚀 开始构建和推送 Docker 镜像..." -ForegroundColor Green
Write-Host "📦 版本: $Version" -ForegroundColor Cyan
Write-Host "🏷️  仓库: $REGISTRY/$USERNAME" -ForegroundColor Cyan
Write-Host ""

# 构建后端镜像
Write-Host "🔨 构建后端镜像..." -ForegroundColor Yellow
docker build -t "$REGISTRY/$USERNAME/aicon-backend:$Version" ./backend
docker tag "$REGISTRY/$USERNAME/aicon-backend:$Version" "$REGISTRY/$USERNAME/aicon-backend:latest"

# 构建前端镜像
Write-Host "🔨 构建前端镜像..." -ForegroundColor Yellow
docker build -t "$REGISTRY/$USERNAME/aicon-frontend:$Version" ./frontend
docker tag "$REGISTRY/$USERNAME/aicon-frontend:$Version" "$REGISTRY/$USERNAME/aicon-frontend:latest"

# 推送镜像
Write-Host "📤 推送后端镜像..." -ForegroundColor Yellow
docker push "$REGISTRY/$USERNAME/aicon-backend:$Version"
docker push "$REGISTRY/$USERNAME/aicon-backend:latest"

Write-Host "📤 推送前端镜像..." -ForegroundColor Yellow
docker push "$REGISTRY/$USERNAME/aicon-frontend:$Version"
docker push "$REGISTRY/$USERNAME/aicon-frontend:latest"

Write-Host ""
Write-Host "✅ 所有镜像已成功推送!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 已推送的镜像:" -ForegroundColor Cyan
Write-Host "   - $REGISTRY/$USERNAME/aicon-backend:$Version"
Write-Host "   - $REGISTRY/$USERNAME/aicon-backend:latest"
Write-Host "   - $REGISTRY/$USERNAME/aicon-frontend:$Version"
Write-Host "   - $REGISTRY/$USERNAME/aicon-frontend:latest"
