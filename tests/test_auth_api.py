# -*- coding: utf-8 -*-
"""本地博客服务——鉴权接口测试（注册 / 登录 / JWT / 当前用户）。

这些用例带 local 标记，仅在 `pytest --env=dev` 时运行；
涉及动态注册、token 透传等有状态链路，采用代码式编排而非 YAML 数据驱动。
"""

import uuid

import allure
import pytest

from app.seed import SEED_PASSWORD, SEED_USERNAME
from utils.assertions import assert_key_exists, assert_status_code, assert_subset
from utils.db import User
from utils.schema_validator import validate_schema

pytestmark = [pytest.mark.local, allure.epic("本地博客服务(FastAPI)"), allure.feature("鉴权接口")]


def _unique_username() -> str:
    return "u" + uuid.uuid4().hex[:10]


@allure.story("用户注册")
class TestRegister:
    def test_register_success(self, http_client, db_inspector):
        username = _unique_username()
        with allure.step("提交合法注册信息"):
            resp = http_client.post(
                "/auth/register", json={"username": username, "password": "Test123456"}
            )

        with allure.step("响应断言：201 且结构符合用户契约"):
            assert_status_code(resp, 201)
            body = resp.json()
            validate_schema(body, "local_user.json")
            assert_subset(body, {"username": username})

        with allure.step("DB断言：用户已落库，且存储的是哈希而非明文密码"):
            row = db_inspector.get(User, username=username)
            assert row is not None, "注册后数据库应能查到用户"
            assert row["password_hash"].startswith("pbkdf2_sha256$"), "密码必须哈希存储"
            assert "Test123456" not in row["password_hash"], "库中不得出现明文密码"

    def test_register_duplicate_username_409(self, http_client):
        with allure.step("用已存在的种子用户名再次注册"):
            resp = http_client.post(
                "/auth/register",
                json={"username": SEED_USERNAME, "password": "Whatever123"},
            )
        assert_status_code(resp, 409)
        assert "已被占用" in resp.json()["detail"]

    @pytest.mark.parametrize(
        "payload, reason",
        [
            ({"username": "ab", "password": "Test123456"}, "用户名短于3位"),
            ({"username": "has space", "password": "Test123456"}, "用户名含非法字符"),
            ({"username": _unique_username(), "password": "123"}, "密码短于6位"),
            ({"username": _unique_username()}, "缺少密码字段"),
        ],
    )
    def test_register_invalid_params_422(self, http_client, payload, reason):
        with allure.step(f"非法入参（{reason}）应被 Pydantic 拦截为 422"):
            resp = http_client.post("/auth/register", json=payload)
        assert_status_code(resp, 422)


@allure.story("用户登录")
class TestLogin:
    def test_login_success_returns_token(self, http_client):
        resp = http_client.post(
            "/auth/login",
            json={"username": SEED_USERNAME, "password": SEED_PASSWORD},
        )
        assert_status_code(resp, 200)
        body = resp.json()
        validate_schema(body, "token.json")

    def test_login_wrong_password_401(self, http_client):
        resp = http_client.post(
            "/auth/login",
            json={"username": SEED_USERNAME, "password": "WrongPass999"},
        )
        assert_status_code(resp, 401)

    def test_login_unknown_user_401(self, http_client):
        resp = http_client.post(
            "/auth/login", json={"username": _unique_username(), "password": "Test123456"}
        )
        assert_status_code(resp, 401)


@allure.story("当前用户与令牌")
class TestCurrentUser:
    def test_me_without_token_401(self, http_client):
        with allure.step("不携带 token 访问受保护接口"):
            resp = http_client.get("/users/me")
        assert_status_code(resp, 401)

    def test_me_with_fake_token_401(self, http_client):
        with allure.step("携带伪造 token"):
            http_client.set_token("fake.token.value")
            resp = http_client.get("/users/me")
        assert_status_code(resp, 401)

    def test_me_with_valid_token_200(self, auth_client):
        client, user_info = auth_client
        with allure.step("用注册登录后获得的 token 访问 /users/me"):
            resp = client.get("/users/me")
        assert_status_code(resp, 200)
        body = resp.json()
        validate_schema(body, "local_user.json")
        assert_subset(body, {"id": user_info["id"], "username": user_info["username"]})
        assert_key_exists(body, "id")
