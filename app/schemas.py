# -*- coding: utf-8 -*-
"""Pydantic 请求/响应模型（FastAPI 自动据此做参数校验，非法时返回 422）。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- 鉴权 ----------
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=64)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


# ---------- 文章 ----------
class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


class PostUpdate(BaseModel):
    """PUT 整体更新，标题与正文都必填。"""

    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    author_id: int
    created_at: datetime
