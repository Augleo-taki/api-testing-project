# -*- coding: utf-8 -*-
"""用户（/users）接口测试用例。"""

import pytest


def test_get_all_users(http_client, base_url):
    """测试获取所有用户"""
    response = http_client.get(f"{base_url}/users")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_single_user(http_client, base_url):
    """测试获取单个用户"""
    user_id = 1
    response = http_client.get(f"{base_url}/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert "name" in data


def test_create_user(http_client, base_url):
    """测试创建用户"""
    new_user = {
        "name": "Test User",
        "username": "testuser",
        "email": "test@example.com",
        "address": {
            "street": "Kulas Light",
            "suite": "Apt. 556",
            "city": "Gwenborough",
            "zipcode": "92998-3874",
            "geo": {
                "lat": "-37.3159",
                "lng": "81.1496"
            }
        },
        "phone": "1-770-736-8031 x56442",
        "website": "hildegard.org",
        "company": {
            "name": "Romaguera-Crona",
            "catchPhrase": "Multi-layered client-server neural-net",
            "bs": "harness real-time e-markets"
        }
    }
    response = http_client.post(f"{base_url}/users", json=new_user)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == new_user["name"]
