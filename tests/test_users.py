# -*- coding: utf-8 -*-
"""用户（/users）接口测试：YAML 数据驱动 + 参数化。"""

import allure
import pytest

from utils.allure_helper import apply_case_labels
from utils.case_runner import run_case
from utils.data_loader import load_yaml

users_cases = load_yaml("data/users_cases.yaml")


@allure.epic("接口自动化测试")
@allure.feature("用户 Users 接口")
class TestUsers:
    @pytest.mark.parametrize(
        "case",
        users_cases,
        ids=[case["case_id"] for case in users_cases],
    )
    def test_users_api(self, http_client, base_url, case):
        apply_case_labels(case)
        run_case(http_client, base_url, case)
