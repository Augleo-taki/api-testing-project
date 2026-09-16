# -*- coding: utf-8 -*-
"""pytest 公共夹具与钩子。

运行环境通过命令行切换：
    pytest                  # 默认 prod（jsonplaceholder）
    pytest --env=dev        # 切到本地 FastAPI（阶段 2 启用）
"""

import sys
from collections.abc import Generator
from pathlib import Path

import pytest

from config.config_manager import load_config
from utils.http_client import HttpClient


def pytest_addoption(parser):
    """注册 --env 命令行参数。"""
    parser.addoption(
        "--env",
        action="store",
        default="prod",
        help="运行环境，对应 config/env 下的配置文件名，默认 prod",
    )


@pytest.fixture(scope="session")
def env_config(request):
    """加载当前运行环境配置（整个会话只加载一次）。"""
    env_name = request.config.getoption("--env")
    return load_config(env_name)


@pytest.fixture(scope="session")
def base_url(env_config) -> str:
    """被测服务基础地址，来源于环境配置。"""
    return env_config["base_url"]


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
