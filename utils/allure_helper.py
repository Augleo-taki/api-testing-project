# -*- coding: utf-8 -*-
"""Allure 动态标签助手：把 YAML 用例里的标题、严重级映射成 Allure 标签。"""

import allure

# YAML 中的 severity 文本 -> Allure 严重级枚举
SEVERITY_MAP = {
    "blocker": allure.severity_level.BLOCKER,
    "critical": allure.severity_level.CRITICAL,
    "normal": allure.severity_level.NORMAL,
    "minor": allure.severity_level.MINOR,
    "trivial": allure.severity_level.TRIVIAL,
}


def apply_case_labels(case: dict) -> None:
    """根据用例数据动态设置 Allure 的 story/title/severity。"""
    allure.dynamic.story(f"{case['method']} {case['path']}")
    allure.dynamic.title(case["title"])
    level = SEVERITY_MAP.get(case.get("severity", "normal"), allure.severity_level.NORMAL)
    allure.dynamic.severity(level)
