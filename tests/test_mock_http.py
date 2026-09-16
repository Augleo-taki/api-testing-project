# -*- coding: utf-8 -*-
"""Mock 打桩测试：用 responses 在 HTTP 协议层拦截请求。

适用场景（为什么需要 Mock）：
- 真实环境很难稳定复现 500、超时、断连等异常，Mock 可以 100% 确定性构造；
- 让用例不依赖网络与外部服务，秒级、稳定、可重复；
- responses 在 requests 发出请求前拦截，请求不会真正到达网络
  （用 responses.calls 可验证请求确实被拦截）。

注意：responses 只能拦截"当前进程内"requests 发出的请求，
因此这里直接对 HttpClient 打桩，不依赖本地服务或外网（任何环境都运行）。
"""

import allure
import pytest
import requests
import responses

from utils.http_client import HttpClient

pytestmark = [
    pytest.mark.mock,
    allure.epic("测试框架能力"),
    allure.feature("Mock 打桩（responses 协议层）"),
]

MOCK_BASE = "http://mock-stub.local"


@responses.activate
@allure.story("正常响应打桩")
def test_mock_get_returns_stubbed_body():
    responses.add(
        responses.GET,
        f"{MOCK_BASE}/posts/1",
        json={"id": 1, "title": "桩数据", "author_id": 7},
        status=200,
    )

    client = HttpClient(base_url=MOCK_BASE, timeout=(1, 1))
    resp = client.get("/posts/1")

    assert resp.status_code == 200
    assert resp.json()["title"] == "桩数据"
    # 关键断言：请求被 responses 拦截，恰好发出 1 次，且未真正出网
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == f"{MOCK_BASE}/posts/1"


@responses.activate
@allure.story("服务端错误打桩")
def test_mock_server_500_passed_through():
    responses.add(
        responses.GET,
        f"{MOCK_BASE}/posts",
        json={"detail": "internal error"},
        status=500,
    )

    client = HttpClient(base_url=MOCK_BASE, timeout=(1, 1))
    resp = client.get("/posts")

    # HttpClient 只负责传输，不吞掉 500；状态码原样返回交由用例断言
    assert resp.status_code == 500
    assert resp.json()["detail"] == "internal error"


@responses.activate
@allure.story("读取超时打桩")
def test_mock_read_timeout_raises():
    # body 传异常实例：requests 发起调用时 responses 直接抛出该异常
    responses.add(
        responses.GET,
        f"{MOCK_BASE}/slow",
        body=requests.exceptions.ReadTimeout("simulated read timeout"),
    )

    client = HttpClient(base_url=MOCK_BASE, timeout=(1, 1))
    with pytest.raises(requests.exceptions.ReadTimeout):
        client.get("/slow")


@responses.activate
@allure.story("连接失败打桩")
def test_mock_connection_error_raises():
    responses.add(
        responses.GET,
        f"{MOCK_BASE}/down",
        body=requests.exceptions.ConnectionError("simulated connection refused"),
    )

    client = HttpClient(base_url=MOCK_BASE, timeout=(1, 1))
    with pytest.raises(requests.exceptions.ConnectionError):
        client.get("/down")


@responses.activate
@allure.story("瞬时故障后恢复（顺序打桩）")
def test_mock_flaky_then_recovered():
    # 对同一 URL 注册两个响应，responses 按注册顺序依次返回：先 500 后 200
    responses.add(responses.GET, f"{MOCK_BASE}/retry", json={"detail": "busy"}, status=500)
    responses.add(responses.GET, f"{MOCK_BASE}/retry", json={"ok": True}, status=200)

    client = HttpClient(base_url=MOCK_BASE, timeout=(1, 1))
    first = client.get("/retry")
    second = client.get("/retry")

    assert first.status_code == 500
    assert second.status_code == 200
    # 说明：业务客户端本身不内置重试；"自动重试 2 次"由 pytest-rerunfailures
    # 在测试框架层完成（见阶段0），二者职责分离。
    assert len(responses.calls) == 2
