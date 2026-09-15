# -*- coding: utf-8 -*-
"""文章（/posts）接口测试用例。"""

import pytest


def test_get_all_posts(http_client, base_url):
    """测试获取所有文章"""
    response = http_client.get(f"{base_url}/posts")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_single_post(http_client, base_url):
    """测试获取单个文章"""
    post_id = 1
    response = http_client.get(f"{base_url}/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post_id
    assert "title" in data


def test_create_post(http_client, base_url):
    """测试创建文章"""
    new_post = {
        "title": "Test Title",
        "body": "This is a test post",
        "userId": 1
    }
    response = http_client.post(f"{base_url}/posts", json=new_post)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == new_post["title"]


def test_update_post(http_client, base_url):
    """测试更新文章"""
    post_id = 1
    updated_post = {
        "id": post_id,
        "title": "Updated Title",
        "body": "Updated content",
        "userId": 1
    }
    response = http_client.put(f"{base_url}/posts/{post_id}", json=updated_post)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == updated_post["title"]


def test_delete_post(http_client, base_url):
    """测试删除文章"""
    post_id = 1
    response = http_client.delete(f"{base_url}/posts/{post_id}")
    assert response.status_code == 200
