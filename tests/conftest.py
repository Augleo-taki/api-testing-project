# -*- coding: utf-8 -*-
"""pytest 公共夹具与钩子。

两套被测环境通过命令行切换，用例按 marker 自动分流：
    pytest              # prod：jsonplaceholder 外网只读接口（无 local 标记的用例）
    pytest --env=dev    # dev：自动拉起本地 FastAPI 服务，只跑带 local 标记的用例
"""

import socket
import subprocess
import sys
import time
import uuid
from collections.abc import Generator
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests

from app.seed import SEED_PASSWORD, SEED_USERNAME
from config.config_manager import load_config
from utils.db import DBInspector
from utils.http_client import HttpClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def pytest_addoption(parser):
    """注册 --env 命令行参数。"""
    parser.addoption(
        "--env",
        action="store",
        default="prod",
        help="运行环境，对应 config/env 下的配置文件名，默认 prod",
    )


def pytest_collection_modifyitems(config, items):
    """按环境自动分流用例。

    标记：local（依赖本地 FastAPI 服务）、mock（HTTP 打桩）、unit（纯单元测试）。
    - dev：运行 local + mock + unit（外网用例跳过）
    - prod（默认）：运行外网无标记用例 + mock + unit（local 跳过）
    mock/unit 不依赖任何真实环境，两种环境下都运行。
    """
    env = config.getoption("--env")

    def has_marker(item, name):
        return item.get_closest_marker(name) is not None

    if env == "dev":
        deselected = [
            item
            for item in items
            if not any(has_marker(item, m) for m in ("local", "mock", "unit"))
        ]
    else:
        deselected = [item for item in items if has_marker(item, "local")]

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = [item for item in items if item not in deselected]


@pytest.fixture(scope="session")
def env_config(request):
    """加载当前运行环境配置（整个会话只加载一次）。"""
    env_name = request.config.getoption("--env")
    return load_config(env_name)


@pytest.fixture(scope="session")
def base_url(env_config) -> str:
    """被测服务基础地址，来源于环境配置。"""
    return env_config["base_url"]


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


@pytest.fixture(scope="session")
def dev_server(env_config) -> Generator[object, None, None]:
    """dev 环境自动拉起 uvicorn 子进程，会话结束后关闭；已手动启动则复用。

    这样跑 `pytest --env=dev` 无需先手动开服务，CI 中也能一键完成。
    """
    if env_config["env_name"] != "dev":
        yield None
        return

    parsed = urlparse(env_config["base_url"])
    host, port = parsed.hostname, parsed.port or 80

    # 端口已被占用：认为服务已由人工启动，直接复用且不负责关闭
    if _is_port_open(host, port):
        yield "external"
        return

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", host, "--port", str(port),
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )

    health_url = f"{env_config['base_url']}/health"
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("本地 uvicorn 服务启动后异常退出")
        try:
            if requests.get(health_url, timeout=1).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.4)
    else:
        proc.kill()
        raise TimeoutError("等待本地服务就绪超时（30s）")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def http_client(env_config) -> Generator[HttpClient, None, None]:
    """统一 HTTP 客户端：超时时间由环境配置决定，用例后自动关闭。

    含 yield 的 fixture 本质是生成器函数：yield 产出客户端供用例使用，
    yield 之后的 close() 在用例结束后执行清理，故返回类型标注为 Generator。
    """
    client = HttpClient(
        base_url=env_config["base_url"],
        timeout=env_config["timeout"],
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def db_inspector(dev_server) -> Generator[DBInspector, None, None]:
    """数据库断言器：依赖 dev_server，确保服务已建表、灌种子后再连接。"""
    inspector = DBInspector()
    yield inspector
    inspector.close()


def _register_and_login(
    client: HttpClient, base_url: str, *, username: str | None = None
) -> dict:
    """注册一个全新用户并登录，返回含 id/username/password/token 的信息。"""
    username = username or ("u" + uuid.uuid4().hex[:10])
    password = "Test123456"

    register_resp = client.post(
        "/auth/register", json={"username": username, "password": password}
    )
    assert register_resp.status_code == 201, register_resp.text
    user_id = register_resp.json()["id"]

    login_resp = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    client.set_token(token)

    return {
        "id": user_id,
        "username": username,
        "password": password,
        "token": token,
    }


@pytest.fixture
def auth_client(
    http_client: HttpClient, dev_server, base_url: str
) -> Generator[tuple[HttpClient, dict], None, None]:
    """已登录的全新用户客户端，返回 (client, 用户信息)，用例后清除凭证。"""
    user_info = _register_and_login(http_client, base_url)
    yield http_client, user_info
    http_client.clear_auth()


@pytest.fixture
def demo_client(
    http_client: HttpClient, dev_server
) -> Generator[HttpClient, None, None]:
    """以种子用户 demo 登录的客户端（文章 id=1、2 的作者）。"""
    resp = http_client.post(
        "/auth/login",
        json={"username": SEED_USERNAME, "password": SEED_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    http_client.set_token(resp.json()["access_token"])
    yield http_client
    http_client.clear_auth()


def pytest_sessionstart(session):
    """会话开始时把环境信息写入 Allure 结果目录（报告首页展示）。

    注意：必须在 sessionstart 而非 configure 阶段写入——Allure 的
    --clean-alluredir 清空动作发生在 configure 阶段，写早了会被清掉。
    """
    config = session.config
    # allure-pytest 注册的选项 dest 为 allure_report_dir（不是 alluredir）
    allure_dir = getattr(config.option, "allure_report_dir", None)
    if not allure_dir:
        return

    env_name = config.option.env
    cfg = load_config(env_name)
    out_dir = Path(allure_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    content = (
        f"Environment={cfg['env_name']}\n"
        f"Base.URL={cfg['base_url']}\n"
        f"Python={sys.version.split()[0]}\n"
    )
    (out_dir / "environment.properties").write_text(content, encoding="utf-8")
