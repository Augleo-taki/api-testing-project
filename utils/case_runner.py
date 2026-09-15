# -*- coding: utf-8 -*-
"""数据驱动用例统一执行器。

YAML 中每条用例的 expected 支持以下断言键（按需组合）：
    status_code   期望 HTTP 状态码，默认 200
    schema        响应体要符合的 JSON Schema 名称（schemas/ 下文件名，不含 .json）
    exact         响应体必须包含的键值子集（递归比较，允许有多余字段）
    length        响应为列表且长度恰好等于该值
    min_length    响应为列表且长度不少于该值
    each_equals   形如 {字段名: 值}，列表每个元素的该字段都等于指定值
    contains_key  响应对象必须包含该字段
"""

import json

import allure

from utils import assertions
from utils.schema_validator import validate_schema


def _attach_json(name: str, payload) -> None:
    """把数据作为 JSON 附件挂到 Allure 报告，方便回溯。"""
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def run_case(client, base_url: str, case: dict) -> None:
    """执行单条 YAML 数据用例并完成全部断言。"""
    method = case["method"].upper()
    url = base_url + case["path"]

    request_kwargs = {}
    if case.get("params"):
        request_kwargs["params"] = case["params"]
    if case.get("body") is not None:
        request_kwargs["json"] = case["body"]

    # 第一步：发请求
    with allure.step(f"发送请求：{method} {case['path']}"):
        _attach_json("请求参数", {"method": method, "url": url, **request_kwargs})
        response = client.request(method, url, **request_kwargs)

    expected = case.get("expected", {})

    # 第二步：校验状态码
    with allure.step(f"校验状态码 = {expected.get('status_code', 200)}"):
        assertions.assert_status_code(response, expected.get("status_code", 200))

    # 第三步：解析并校验响应体
    with allure.step("校验响应内容"):
        data = response.json()
        _attach_json("实际响应", data)

        if "schema" in expected:
            with allure.step(f"校验响应结构 schema = {expected['schema']}"):
                validate_schema(data, expected["schema"])

        if "exact" in expected:
            assertions.assert_subset(data, expected["exact"])

        if "length" in expected:
            assertions.assert_length(data, expected["length"])

        if "min_length" in expected:
            assertions.assert_min_length(data, expected["min_length"])

        if "each_equals" in expected:
            for field, value in expected["each_equals"].items():
                assertions.assert_each_equals(data, field, value)

        if "contains_key" in expected:
            assertions.assert_key_exists(data, expected["contains_key"])
