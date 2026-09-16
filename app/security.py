# -*- coding: utf-8 -*-
"""安全模块：密码哈希（PBKDF2，标准库实现）与 JWT 签发/解析。

说明：教学项目用标准库 hashlib 的 PBKDF2-HMAC-SHA256，避免额外原生依赖；
生产环境通常使用 bcrypt / argon2id。JWT 密钥在真实项目中必须来自环境变量。
"""

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

# 仅用于本地教学服务的固定密钥；生产环境务必改为从环境变量读取
SECRET_KEY = "dev-only-secret-key-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

_PBKDF2_ROUNDS = 260_000


def hash_password(password: str) -> str:
    """生成 'pbkdf2_sha256$迭代次数$盐$哈希' 形式的密码串。"""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS
    )
    return (
        f"pbkdf2_sha256${_PBKDF2_ROUNDS}"
        f"${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"
    )


def verify_password(password: str, stored: str) -> bool:
    """校验密码与存储的哈希串是否匹配（使用恒定时间比较防时序攻击）。"""
    try:
        _algo, rounds, salt_b64, hash_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(rounds)
        )
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    """为指定用户签发 JWT。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    """解析并校验 JWT，返回用户 ID；无效/过期抛出 jwt 异常。"""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload["sub"])
