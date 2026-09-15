# -*- coding: utf-8 -*-
"""环境配置管理器：按环境名加载 config/env/<env>.yaml。

用法：
    cfg = load_config("prod")
    cfg["base_url"]、cfg["timeout"]
命令行通过 pytest --env=prod|dev 切换，默认 prod。
"""

from functools import lru_cache
from pathlib import Path

import yaml

# 项目根目录（本文件位于 config/ 下）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_DIR = Path(__file__).resolve().parent / "env"


def available_envs() -> list[str]:
    """列出所有可用环境名。"""
    return sorted(p.stem for p in ENV_DIR.glob("*.yaml"))


@lru_cache(maxsize=None)  # 同一环境只读取一次文件
def load_config(env: str) -> dict:
    """加载指定环境配置，timeout 转换为 requests 要求的 (连接, 读取) 元组。"""
    config_path = ENV_DIR / f"{env}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"环境 '{env}' 的配置文件不存在：{config_path}；"
            f"当前可选环境：{available_envs()}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    timeout_cfg = cfg.get("timeout", {"connect": 5, "read": 10})
    cfg["timeout"] = (float(timeout_cfg["connect"]), float(timeout_cfg["read"]))
    return cfg
