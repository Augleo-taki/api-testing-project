# -*- coding: utf-8 -*-
"""FastAPI 应用入口。

本地启动：
    uvicorn app.main:app --reload
文档（自动生成）：
    http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import auth, posts
from app.seed import reset_and_seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 启动时重建表并灌入种子数据，保证每次启动环境干净、可重复测试
    reset_and_seed()
    yield


app = FastAPI(
    title="接口测试练习服务",
    description="供自动化测试练习的博客后端：JWT 鉴权 + SQLite 落库 + 文章权限控制",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(posts.router)


@app.get("/health", tags=["系统"])
def health():
    """健康检查，测试框架据此判断服务是否就绪。"""
    return {"status": "ok"}
