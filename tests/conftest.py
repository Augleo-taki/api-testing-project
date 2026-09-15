# -*- coding: utf-8 -*-
"""pytest 公共夹具（fixtures）。

注意：fixture 不需要在用例文件里 import，
pytest 会按参数名自动把 fixture 注入到用例函数中。
"""

import pytest

from utils.http_client import HttpClient


@pytest.fixture(scope="session")
def base_url() -> str:
    """被测服务基础地址（常量，整个测试会话只创建一次）。"""
    return "https://jsonplaceholder.typicode.com"


@pytest.fixture
def http_client(base_url: str) -> HttpClient:
    """提供统一 HTTP 客户端：默认 10s 超时，自动记录请求日志。

    函数级作用域：每个用例拿到独立客户端，用例之间互不影响；
    用例结束后自动关闭底层连接。
    """
    client = HttpClient(base_url=base_url, timeout=10.0)
    yield client
    client.close()
