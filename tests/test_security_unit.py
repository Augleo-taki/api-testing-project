# -*- coding: utf-8 -*-
"""安全模块纯单元测试（不启动服务、不发 HTTP，任何环境都运行）。

与接口测试的区别：直接调用被测函数，速度最快、定位最精确；
其中用 pytest-mock 的 mocker.patch 在函数层打桩，模拟"令牌过期"
这类无法靠真实等待复现的场景。
"""

import jwt
import pytest
import allure

from app.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

pytestmark = [
    pytest.mark.unit,
    allure.epic("本地博客服务(FastAPI)"),
    allure.feature("安全模块单元测试"),
]


@allure.story("密码哈希")
class TestPasswordHash:
    def test_hash_and_verify_match(self):
        stored = hash_password("MyPass123")
        assert verify_password("MyPass123", stored) is True

    def test_wrong_password_rejected(self):
        stored = hash_password("MyPass123")
        assert verify_password("WrongPass", stored) is False

    def test_hash_is_salted_and_hides_plaintext(self):
        plain = "SamePass123"
        h1 = hash_password(plain)
        h2 = hash_password(plain)

        assert h1 != h2, "加盐后同一密码两次哈希结果应不同"
        assert plain not in h1 and plain not in h2, "哈希串中不得出现明文"
        assert verify_password(plain, h1) and verify_password(plain, h2)

    def test_verify_malformed_hash_returns_false(self):
        assert verify_password("anything", "not-a-valid-hash") is False


@allure.story("JWT 令牌")
class TestJwt:
    def test_create_and_decode_roundtrip(self):
        token = create_access_token(42)
        assert decode_access_token(token) == 42

    def test_tampered_token_rejected(self):
        token = create_access_token(1)
        # 篡改签名末尾字符
        tampered = token[:-3] + ("aaa" if token[-3:] != "aaa" else "bbb")
        with pytest.raises(jwt.PyJWTError):
            decode_access_token(tampered)

    def test_garbage_token_rejected(self):
        with pytest.raises(jwt.PyJWTError):
            decode_access_token("not.a.valid.jwt")

    def test_token_signed_with_other_secret_rejected(self):
        forged = jwt.encode(
            {"sub": "1"},
            "forged-attacker-secret-key-0123456789-abcdef-xyz",
            algorithm=ALGORITHM,
        )
        with pytest.raises(jwt.PyJWTError):
            decode_access_token(forged)

    def test_expired_token_rejected(self, mocker):
        # 函数层打桩：把有效期常量改成 -10 分钟，签发即过期，无需真实等待
        mocker.patch("app.security.ACCESS_TOKEN_EXPIRE_MINUTES", -10)
        expired_token = create_access_token(1)

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(expired_token)

    def test_secret_key_strength_check(self):
        # 提醒项：教学固定密钥可跑通；生产必须从环境变量注入强随机密钥
        assert isinstance(SECRET_KEY, str) and len(SECRET_KEY) >= 16
