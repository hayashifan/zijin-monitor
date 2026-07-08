# 紫金单股监控器 - 多阶段构建
# Stage 1: 前端构建
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: 后端运行
FROM python:3.11-slim AS backend
WORKDIR /app

# 安装 Python 依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 复制配置文件
COPY config/ ./config/

# 复制前端构建产物（静态文件由 nginx 服务）
COPY --from=frontend-build /app/frontend/dist ./static/

# 创建数据目录
RUN mkdir -p /data

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3002/health')" || exit 1

EXPOSE 3002

CMD ["python", "main.py"]
