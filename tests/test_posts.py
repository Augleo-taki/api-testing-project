# -*- coding: utf-8 -*-
"""文章（/posts）接口测试：YAML 数据驱动 + 参数化。"""

import allure
import pytest

from utils.allure_helper import apply_case_labels
from utils.case_runner import run_case
from utils.data_loader import load_yaml

# 模块加载时读取用例数据（parametrize 需要在收集阶段拿到）
posts_cases = load_yaml("data/posts_cases.yaml")


@allure.epic("接口自动化测试")
@allure.feature("文章 Posts 接口")
class TestPosts:
    @pytest.mark.parametrize(
        "case",
        posts_cases,
        ids=[case["case_id"] for case in posts_cases],
    )
    def test_posts_api(self, http_client, base_url, case):
        # 每条参数化用例动态生成 Allure 标题与严重级
        apply_case_labels(case)
        run_case(http_client, base_url, case)
