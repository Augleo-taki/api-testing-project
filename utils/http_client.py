# -*- coding: utf-8 -*-
"""统一 HTTP 客户端封装。

为什么需要这一层：
1. 给所有请求统一设置 timeout，避免接口无响应时程序无限等待；
2. 统一记录请求/响应日志，方便排查失败用例；
3. 后续接口对象层（api/）只需要面向 HttpClient 编程，
   换域名、加鉴权头、改公共逻辑时只改这一处。
"""

import logging

import requests

logger = logging.getLogger("http_client")


class HttpClient:
    """对 requests.Session 的薄封装，方法签名与 requests 保持一致。"""

    def __init__(
        self,
        base_url: str = "",
        timeout: "float | tuple[float, float]" = (5.0, 10.0),
    ):
        # base_url 允许为空：此时请求时需传入完整 URL（当前用例的写法）
        self.base_url = base_url.rstrip("/")
        # requests 的 timeout 支持元组：(连接超时, 读取超时)
        # 连接超时：建立 TCP/TLS 连接的最长等待（你遇到的握手卡住就归它管）
        # 读取超时：服务器两次响应数据包之间的最长间隔
        self.timeout = timeout
        self._session = requests.Session()

    def _build_url(self, url_or_path: str) -> str:
        """传入完整 URL 时原样返回；传入相对路径时拼接 base_url。"""
        if url_or_path.startswith(("http://", "https://")):
            return url_or_path
        if not self.base_url:
            raise ValueError("未配置 base_url，请求必须传入完整 URL")
        return f"{self.base_url}/{url_or_path.lstrip('/')}"

    def request(self, method: str, url_or_path: str, **kwargs) -> requests.Response:
        # setdefault：调用方单独传了 timeout 时以调用方为准，否则用默认值
        kwargs.setdefault("timeout", self.timeout)
        url = self._build_url(url_or_path)

        logger.info("--> %s %s", method.upper(), url)
        try:
            response = self._session.request(method, url, **kwargs)
        except requests.RequestException as exc:
            # 超时、连接失败等网络异常：记录后原样抛出，让用例明确失败
            logger.error("--> %s %s 请求异常: %s", method.upper(), url, exc)
            raise

        elapsed = response.elapsed.total_seconds()
        logger.info(
            "<-- %s %s 状态码=%s 耗时=%.3fs",
            method.upper(), url, response.status_code, elapsed,
        )
        return response

    def get(self, url_or_path: str, **kwargs) -> requests.Response:
        return self.request("GET", url_or_path, **kwargs)

    def post(self, url_or_path: str, **kwargs) -> requests.Response:
        return self.request("POST", url_or_path, **kwargs)

    def put(self, url_or_path: str, **kwargs) -> requests.Response:
        return self.request("PUT", url_or_path, **kwargs)

    def patch(self, url_or_path: str, **kwargs) -> requests.Response:
        return self.request("PATCH", url_or_path, **kwargs)

    def delete(self, url_or_path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", url_or_path, **kwargs)

    def set_token(self, token: str) -> None:
        """设置登录令牌，之后该客户端的所有请求自动携带
        Authorization: Bearer <token>。"""
        self._session.headers["Authorization"] = f"Bearer {token}"

    def clear_auth(self) -> None:
        """清除登录令牌，恢复为匿名客户端。"""
        self._session.headers.pop("Authorization", None)

    def close(self) -> None:
        self._session.close()
