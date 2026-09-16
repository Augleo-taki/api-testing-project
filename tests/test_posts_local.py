# -*- coding: utf-8 -*-
"""本地博客服务——文章接口测试（CRUD、JWT 鉴权、越权防护、DB 双校验）。

仅在 `pytest --env=dev` 时运行。种子数据：用户 demo(id=1) 拥有文章 id=1、2。
"""

import allure
import pytest

from utils.assertions import (
    assert_each_equals,
    assert_key_exists,
    assert_length,
    assert_min_length,
    assert_status_code,
    assert_subset,
)
from utils.db import Post
from utils.schema_validator import validate_schema

pytestmark = [pytest.mark.local, allure.epic("本地博客服务(FastAPI)"), allure.feature("文章接口")]


@allure.story("文章查询（公开）")
class TestPostQuery:
    def test_list_seed_posts(self, http_client):
        resp = http_client.get("/posts")
        assert_status_code(resp, 200)
        data = resp.json()
        assert_min_length(data, 2)
        for item in data:
            validate_schema(item, "local_post.json")

    def test_get_single_seed_post(self, http_client):
        resp = http_client.get("/posts/1")
        assert_status_code(resp, 200)
        body = resp.json()
        validate_schema(body, "local_post.json")
        assert_subset(body, {"id": 1, "author_id": 1})

    def test_get_post_not_found_404(self, http_client):
        resp = http_client.get("/posts/999999")
        assert_status_code(resp, 404)

    def test_pagination_limit_and_skip(self, http_client):
        with allure.step("limit=1 只返回 1 条"):
            r1 = http_client.get("/posts", params={"limit": 1})
            assert_status_code(r1, 200)
            assert_length(r1.json(), 1)

        with allure.step("skip=1&limit=1 按 id 排序应取到种子文章 id=2"):
            r2 = http_client.get("/posts", params={"skip": 1, "limit": 1})
            assert_status_code(r2, 200)
            assert_subset(r2.json()[0], {"id": 2})

    def test_filter_by_author(self, auth_client):
        client, user = auth_client
        with allure.step("当前用户先创建一篇文章"):
            created = client.post("/posts", json={"title": "作者过滤", "body": "内容"})
            assert_status_code(created, 201)

        with allure.step("按 author_id 过滤，结果全部属于该用户"):
            resp = client.get("/posts", params={"author_id": user["id"]})
            assert_status_code(resp, 200)
            rows = resp.json()
            assert_min_length(rows, 1)
            assert_each_equals(rows, "author_id", user["id"])


@allure.story("文章创建（需登录）")
class TestPostCreate:
    def test_create_without_token_401(self, http_client, db_inspector):
        before = db_inspector.count(Post)
        resp = http_client.post("/posts", json={"title": "匿名投稿", "body": "内容"})
        assert_status_code(resp, 401)
        with allure.step("DB断言：被拦截后文章数不增加"):
            assert db_inspector.count(Post) == before

    def test_create_with_fake_token_401(self, http_client):
        http_client.set_token("not.a.real.token")
        resp = http_client.post("/posts", json={"title": "伪造", "body": "内容"})
        assert_status_code(resp, 401)

    def test_create_success_with_db_check(self, auth_client, db_inspector):
        client, user = auth_client
        payload = {"title": "我的第一篇", "body": "正文内容ABC"}
        with allure.step("登录后创建文章"):
            resp = client.post("/posts", json=payload)
        assert_status_code(resp, 201)
        body = resp.json()
        validate_schema(body, "local_post.json")
        post_id = body["id"]

        with allure.step("响应断言：作者为当前登录用户"):
            assert_subset(body, {"title": payload["title"], "body": payload["body"],
                                 "author_id": user["id"]})

        with allure.step("DB断言：文章真正落库且字段一致"):
            row = db_inspector.get(Post, id=post_id)
            assert row is not None, "创建后数据库应能查到文章"
            assert row["title"] == payload["title"]
            assert row["body"] == payload["body"]
            assert row["author_id"] == user["id"]

    def test_create_empty_title_422_no_db_write(self, auth_client, db_inspector):
        client, _ = auth_client
        before = db_inspector.count(Post)
        resp = client.post("/posts", json={"title": "", "body": "内容"})
        assert_status_code(resp, 422)
        with allure.step("DB断言：校验失败不落库，文章数不变"):
            assert db_inspector.count(Post) == before


@allure.story("文章修改与删除（需登录且为作者）")
class TestPostUpdateDelete:
    def test_update_others_post_403(self, auth_client, db_inspector):
        client, _ = auth_client
        with allure.step("新用户尝试修改 demo 的文章 id=1"):
            resp = client.put("/posts/1", json={"title": "恶意改名", "body": "x"})
        assert_status_code(resp, 403)
        with allure.step("DB断言：他人文章标题未被篡改"):
            assert db_inspector.get(Post, id=1)["title"] == "第一篇博客"

    def test_delete_others_post_403(self, auth_client, db_inspector):
        client, _ = auth_client
        resp = client.delete("/posts/1")
        assert_status_code(resp, 403)
        assert db_inspector.exists(Post, id=1), "他人文章不应被删除"

    def test_update_nonexistent_404(self, demo_client):
        resp = demo_client.put("/posts/999999", json={"title": "x", "body": "y"})
        assert_status_code(resp, 404)

    def test_full_crud_flow_with_db_check(self, auth_client, db_inspector):
        client, user = auth_client

        with allure.step("Create：创建"):
            created = client.post("/posts", json={"title": "原标题", "body": "原正文"})
            assert_status_code(created, 201)
            post_id = created.json()["id"]
            assert db_inspector.exists(Post, id=post_id)

        with allure.step("Read：能查到"):
            got = client.get(f"/posts/{post_id}")
            assert_status_code(got, 200)
            assert_subset(got.json(), {"id": post_id, "title": "原标题"})

        with allure.step("Update：作者本人修改，响应与DB均更新"):
            updated = client.put(f"/posts/{post_id}", json={"title": "新标题", "body": "新正文"})
            assert_status_code(updated, 200)
            assert_subset(updated.json(), {"title": "新标题", "body": "新正文"})
            row = db_inspector.get(Post, id=post_id)
            assert row["title"] == "新标题" and row["body"] == "新正文"

        with allure.step("Delete：作者本人删除"):
            deleted = client.delete(f"/posts/{post_id}")
            assert_status_code(deleted, 200)
            assert_key_exists(deleted.json(), "message")

        with allure.step("DB断言：删除后接口404且库中无记录"):
            assert_status_code(client.get(f"/posts/{post_id}"), 404)
            assert db_inspector.get(Post, id=post_id) is None
