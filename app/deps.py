# -*- coding: utf-8 -*-
"""公共依赖：从 Bearer Token 解析当前登录用户。"""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

# tokenUrl 仅用于 OpenAPI 文档的 Authorize 按钮
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """校验 JWT 并返回用户对象；任何问题统一抛 401。"""
    credentials_exc = HTTPException(
        status_code=401,
        detail="无效或过期的登录凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_exc

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exc
    return user
