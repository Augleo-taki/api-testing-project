# api-testing-project

基于 **Python + pytest + requests** 的接口自动化测试练习项目，被测对象为公开练习 API
[JSONPlaceholder](https://jsonplaceholder.typicode.com/)，覆盖用户（users）与文章（posts）
两类资源的增删改查（CRUD）接口。

## 技术栈

| 用途 | 技术 / 工具 |
| --- | --- |
| 编程语言 | Python 3.13 |
| 测试框架 | pytest 9.1.1 |
| HTTP 请求 | requests 2.34.2（统一封装，连接/读取双超时 + 请求日志） |
| 测试报告 | Allure（allure-pytest 2.16.0）、pytest-html 4.2.0 |
| 失败重试 | pytest-rerunfailures 16.6.1（仅网络异常自动重试，断言失败不重试） |

## 目录结构

```text
api-testing-project/
├── pytest.ini              # pytest 全局配置（用例发现、实时日志、失败重试、导入路径）
├── requirements.txt        # 项目依赖，版本已锁定
├── .gitignore              # 忽略缓存、虚拟环境与报告产物
├── utils/
│   ├── __init__.py
│   └── http_client.py      # HttpClient：统一超时、请求/响应日志、Session 复用
└── tests/
    ├── conftest.py         # 公共 fixture：base_url、http_client
    ├── test_users.py       # /users 接口用例（3 条）
    ├── test_posts.py       # /posts 接口用例（5 条）
    └── reports/            # 报告输出目录（运行后生成，不纳入 git）
```

## 环境准备

```bash
# 1. 建议使用虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt
```

## 运行测试

```bash
# 在项目根目录执行全部用例（pytest.ini 已固化默认参数）
pytest

# 只运行某个用例文件
pytest tests/test_posts.py

# 按关键字匹配运行
pytest -k "user"
```

### 生成测试报告

```bash
# 方式一：pytest-html 单文件报告
pytest --html=tests/reports/test_report.html --self-contained-html

# 方式二：Allure 报告（需先安装 Allure 命令行，依赖 Java 环境）
pytest --alluredir=tests/reports/allure
allure serve tests/reports/allure
```

## 用例清单

| 模块 | 用例 | 接口 | 说明 |
| --- | --- | --- | --- |
| users | test_get_all_users | GET /users | 查询用户列表非空 |
| users | test_get_single_user | GET /users/{id} | 查询单个用户并校验字段 |
| users | test_create_user | POST /users | 创建用户并回显校验 |
| posts | test_get_all_posts | GET /posts | 查询文章列表非空 |
| posts | test_get_single_post | GET /posts/{id} | 查询单篇文章并校验字段 |
| posts | test_create_post | POST /posts | 创建文章并回显校验 |
| posts | test_update_post | PUT /posts/{id} | 更新文章并校验回显 |
| posts | test_delete_post | DELETE /posts/{id} | 删除文章校验状态码 |

## 设计说明

- **统一 HTTP 封装**：所有请求经由 `utils/http_client.py` 的 `HttpClient` 发出，
  统一设置 (5s 连接, 10s 读取) 双超时（避免接口无响应时无限等待），并记录请求方法、
  URL、响应状态码与耗时。
- **失败重试策略**：通过 pytest-rerunfailures 对网络抖动类异常（超时、连接错误等）
  自动重试 2 次、每次间隔 1s；业务断言失败不会重试，避免掩盖真实缺陷（配置见 `pytest.ini`）。
- **fixture 注入**：`base_url`、`http_client` 在 `conftest.py` 中定义，用例按参数名声明即可，
  无需 import；`http_client` 为函数级，保证用例之间互不影响，结束后自动关闭连接。
