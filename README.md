# api-testing-project

基于 **Python + pytest + requests** 的分层接口自动化测试框架，被测对象为公开练习 API
[JSONPlaceholder](https://jsonplaceholder.typicode.com/)，覆盖用户（users）与文章（posts）
两类资源。框架采用 **YAML 数据驱动**，用例与代码分离；结合等价类、边界值等方法设计
正向 / 边界 / 负向用例，并用 JSON Schema 校验响应结构，Allure 报告按 epic/feature/story/
severity 分级展示。

## 技术栈

| 用途 | 技术 / 工具 |
| --- | --- |
| 编程语言 | Python 3.13 |
| 测试框架 | pytest 9.1.1（parametrize 数据驱动） |
| HTTP 请求 | requests 2.34.2（统一封装，连接/读取双超时 + 请求日志） |
| 数据/配置 | PyYAML 6.0.3（用例数据、多环境配置） |
| 结构校验 | jsonschema 4.26.0（Draft-07 响应结构校验） |
| 测试报告 | Allure（allure-pytest 2.16.0）、pytest-html 4.2.0 |
| 失败重试 | pytest-rerunfailures 16.6.1（仅网络异常重试，断言失败不重试） |

## 目录结构

```text
api-testing-project/
├── pytest.ini               # pytest 配置（发现规则、实时日志、失败重试、导入路径）
├── requirements.txt         # 依赖版本锁定
├── .gitignore
├── config/                  # 多环境配置层
│   ├── config_manager.py    #   按环境名加载配置
│   └── env/
│       ├── prod.yaml        #   公共练习环境（默认）
│       └── dev.yaml         #   本地环境（阶段2自建服务后 --env=dev 切换）
├── data/                    # 用例数据层（YAML，与代码分离）
│   ├── posts_cases.yaml     #   文章 15 条：正向/边界/负向
│   └── users_cases.yaml     #   用户 8 条：正向/边界/负向
├── schemas/                 # 响应结构契约（JSON Schema）
│   ├── post.json / post_list.json
│   └── user.json / user_list.json
├── utils/                   # 公共能力层
│   ├── http_client.py       #   HttpClient：双超时、请求日志、Session 复用
│   ├── assertions.py        #   语义化断言（状态码/子集/长度/逐元素等）
│   ├── schema_validator.py  #   Schema 加载与校验（错误一次性汇总）
│   ├── case_runner.py       #   数据驱动用例统一执行器（含 Allure 步骤）
│   ├── data_loader.py       #   YAML 加载
│   └── allure_helper.py     #   Allure 动态标题/严重级
└── tests/                   # 用例层（极薄，只负责参数化与调度）
    ├── conftest.py          #   --env 参数、环境配置与客户端 fixture
    ├── test_posts.py        #   文章接口（15 条参数化用例）
    └── test_users.py        #   用户接口（8 条参数化用例）
```

## 环境准备

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```

## 运行测试

```bash
pytest                            # 默认 prod 环境，运行全部 23 条用例
pytest --env=dev                  # 切换到 config/env/dev.yaml 指定的环境
pytest tests/test_posts.py        # 只跑文章模块
pytest -k not_found              # 按用例 ID 关键字筛选（示例：资源不存在类）
pytest --collect-only             # 只收集不执行，查看参数化展开后的用例清单
```

### 生成测试报告

```bash
# pytest-html 单文件报告
pytest --html=tests/reports/test_report.html --self-contained-html

# Allure 报告（需 Allure 命令行 + Java）
pytest --alluredir=tests/reports/allure --clean-alluredir
allure serve tests/reports/allure
```

## 用例设计概览（共 23 条）

| 模块 | 正向 | 边界/负向/特性 | 小计 | 覆盖设计点 |
| --- | --- | --- | --- | --- |
| posts | 8 | 7 | 15 | CRUD、过滤、分页、ID 边界值（0/负数/非数字/越界）、404、空列表、删除幂等 |
| users | 4 | 4 | 8 | 列表/详情、嵌套结构校验、条件命中与未命中、ID 边界、宽松创建 |

用例断言均基于对接口真实行为的探测，例如：路径资源不存在返回 **404+空对象**，
而条件过滤无结果返回 **200+空列表**；空请求体创建仍返回 201（服务端未校验必填，
作为需求疑点在用例中记录）。

## 框架设计说明

- **数据驱动（核心）**：用例数据写在 `data/*.yaml`，新增用例只需加一段 YAML，无需改 Python；
  `case_runner` 统一完成发请求与状态码/schema/字段/长度等断言，并自动生成 Allure 步骤与请求、
  响应附件。
- **JSON Schema 契约校验**：不只断言个别字段，而是用 `schemas/*.json` 校验类型、必填、嵌套对象
  与正则（如邮箱），结构异常时一次性汇总全部错误。
- **分层设计**：用例层 / 数据层 / 公共能力层 / 配置层职责分离，后续接入新接口成本极低。
- **多环境配置**：`config/env/*.yaml` 管理各环境地址与超时，`--env` 一键切换。
- **稳定性保障**：双超时 + 仅对网络异常自动重试 2 次，业务断言失败不重试，避免掩盖缺陷。
