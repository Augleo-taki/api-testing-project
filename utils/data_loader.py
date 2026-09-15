# -*- coding: utf-8 -*-
"""测试数据（YAML）加载工具。"""

from pathlib import Path

import yaml

# 项目根目录（本文件位于 utils/ 下）
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_yaml(rel_path: str):
    """按相对于项目根目录的路径加载 YAML，返回 list/dict。"""
    file_path = (PROJECT_ROOT / rel_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"测试数据文件不存在：{file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
