# -*- coding: utf-8 -*-
"""JSON Schema 响应结构校验封装。"""

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


@lru_cache(maxsize=None)
def load_schema(schema_name: str) -> dict:
    """按名称加载 schema，允许省略 .json 后缀，结果缓存。"""
    if not schema_name.endswith(".json"):
        schema_name += ".json"
    schema_path = SCHEMA_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema 文件不存在：{schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(instance, schema_name: str) -> None:
    """用指定 schema 校验响应实例；不通过时汇总全部错误并抛出 AssertionError。"""
    schema = load_schema(schema_name)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))

    if errors:
        lines = []
        for err in errors:
            location = ".".join(str(p) for p in err.absolute_path) or "(根对象)"
            lines.append(f"  - 路径 {location}：{err.message}")
        raise AssertionError(
            f"响应结构不符合 schema [{schema_name}]，共 {len(errors)} 处问题：\n"
            + "\n".join(lines)
        )
