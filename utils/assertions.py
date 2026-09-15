# -*- coding: utf-8 -*-
"""语义化通用断言：用例层只表达"断言什么"，不关心实现细节。"""


def assert_status_code(response, expected_code: int) -> None:
    """断言 HTTP 状态码。"""
    actual = response.status_code
    assert actual == expected_code, (
        f"状态码不符合预期：期望 {expected_code}，实际 {actual}；"
        f"响应体：{response.text[:200]}"
    )


def assert_subset(actual, expected, path: str = "$") -> None:
    """递归断言"子集包含"：actual 必须包含 expected 的全部键值（允许 actual 有多余字段）。

    - dict：逐键递归；
    - list：按下标递归（只校验 expected 列出的位置）；
    - 其他标量：直接比较。
    """
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}：期望是对象，实际是 {type(actual).__name__}"
        for key, exp_val in expected.items():
            assert key in actual, f"{path}：缺少字段 '{key}'，实际字段 {list(actual.keys())}"
            assert_subset(actual[key], exp_val, f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list), f"{path}：期望是数组，实际是 {type(actual).__name__}"
        assert len(actual) >= len(expected), (
            f"{path}：数组长度不足，期望至少 {len(expected)}，实际 {len(actual)}"
        )
        for index, exp_val in enumerate(expected):
            assert_subset(actual[index], exp_val, f"{path}[{index}]")
    else:
        assert actual == expected, f"{path}：期望 {expected!r}，实际 {actual!r}"


def assert_length(data, expected_length: int) -> None:
    """断言容器长度恰好等于期望值。"""
    actual_length = len(data)
    assert actual_length == expected_length, (
        f"长度不符合预期：期望 {expected_length}，实际 {actual_length}"
    )


def assert_min_length(data, min_length: int) -> None:
    """断言容器长度不少于期望值。"""
    actual_length = len(data)
    assert actual_length >= min_length, (
        f"长度不满足下限：期望至少 {min_length}，实际 {actual_length}"
    )


def assert_each_equals(items: list, field: str, expected) -> None:
    """断言列表中每个元素的指定字段都等于期望值（用于过滤类接口）。"""
    assert len(items) > 0, "列表为空，无法逐元素校验"
    for index, item in enumerate(items):
        assert item.get(field) == expected, (
            f"第 {index} 个元素的字段 '{field}' 不符合预期："
            f"期望 {expected!r}，实际 {item.get(field)!r}"
        )


def assert_key_exists(data, key: str) -> None:
    """断言对象包含指定字段。"""
    assert key in data, f"响应缺少字段 '{key}'，实际字段 {list(data.keys())}"
