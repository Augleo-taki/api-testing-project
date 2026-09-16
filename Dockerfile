# 被测服务镜像（FastAPI + Uvicorn）
FROM python:3.13-slim

# 不缓冲日志、不生成 .pyc，容器内日志即时可见
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先单独复制依赖文件，利用 Docker 分层缓存，改代码不必重装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 只复制被测服务代码
COPY app ./app

EXPOSE 8000

# 0.0.0.0 使容器外可通过端口映射访问
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
