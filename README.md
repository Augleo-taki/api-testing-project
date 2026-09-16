# api-testing-project

基于 **Python + pytest + requests** 的分层接口自动化测试项目，包含两个被测对象：

1. **公开练习 API** [JSONPlaceholder](https://jsonplaceholder.typicode.com/)（prod 环境）：
   用 **YAML 数据驱动**测试 users / posts，结合等价类、边界值设计正/负向用例，JSON Schema 校验响应。
2. **自建被测服务**（dev 环境）：用 **FastAPI + SQLite + JWT** 实现的博客后端，覆盖注册登录、
   令牌鉴权、文章 CRUD、越权防护，并做**响应断言 + 数据库断言双校验**；测试时框架自动启停服务，
   本地秒级跑完，摆脱对外网的依赖。

两套用例通过 `local` 标记 + `--env` 参数**自动分流**，共 48 条用例。

## 技术栈

| 用途 | 技术 / 工具 |
| --- | --- |
| 编程语言 | Python 3.13 |
| 测试框架 | pytest 9.1.1（parametrize 数据驱动、fixture、marker 分流） |
| HTTP 请求 | requests 2.34.2（统一封装，双超时、请求日志、JWT 透传） |
| 被测服务 | FastAPI 0.141 + Uvicorn 0.53 |
| 数据库 / ORM | SQLite + SQLAlchemy 2.0（落库与 DB 断言） |
| 鉴权 | JWT（PyJWT 2.14）+ PBKDF2 密码哈希 |
| 数据/配置 | PyYAML 6.0.3（用例数据、多环境配置） |
| 结构校验 | jsonschema 4.26.0（Draft-07 响应契约校验） |
| 测试报告 | Allure（allure-pytest 2.16.0）、pytest-html 4.2.0 |
| 失败重试 | pytest-rerunfailures 16.6.1（仅网络异常重试，断言失败不重试） |

## 目录结构

```text
api-testing-project/
├── app/                     # 【阶段2】被测服务（SUT）：FastAPI 博客后端
│   ├── main.py              #   应用入口、健康检查、启动时建表灌种子
│   ├── database.py          #   SQLite 引擎与会话
│   ├── models.py            #   ORM 模型：User / Post
│   ├── schemas.py           #   Pydantic 请求/响应模型（自动 422 校验）
│   ├── security.py          #   密码哈希与 JWT 签发/解析
│   ├── deps.py              #   依赖：从 Bearer Token 解析当前用户
│   ├── seed.py              #   种子数据（demo 用户 + 2 篇文章）
│   └── routers/             #   路由：auth（注册/登录/me）、posts（CRUD+权限）
├── config/                  # 多环境配置层
│   ├── config_manager.py
│   └── env/
│       ├── prod.yaml        #   公共练习环境（默认，超时 5/10s）
│       └── dev.yaml         #   本地服务 http://127.0.0.1:8000（超时 2/5s）
├── data/                    # 外网用例数据层（YAML，与代码分离）
│   ├── posts_cases.yaml     #   文章 15 条
│   └── users_cases.yaml     #   用户 8 条
├── schemas/                 # 响应结构契约（JSON Schema）
│   ├── post.json / user.json / ...        # 外网契约
│   ├── local_post.json / local_user.json / token.json   # 本地服务契约
├── utils/                   # 公共能力层
│   ├── http_client.py       #   HttpClient：双超时、日志、set_token 鉴权透传
│   ├── db.py                #   【阶段2】DBInspector：数据库计数/查询断言
│   ├── assertions.py        #   语义化断言
│   ├── schema_validator.py  #   Schema 加载与校验
│   ├── case_runner.py       #   数据驱动用例统一执行器
│   ├── data_loader.py / allure_helper.py
└── tests/
    ├── conftest.py          #   --env、服务自动启停、登录态/DB fixture、用例分流
    ├── test_posts.py / test_users.py        # prod 外网 23 条（YAML 驱动）
    ├── test_auth_api.py                     # dev 鉴权 10 条（代码编排）
    └── test_posts_local.py                  # dev 文章 15 条（含 DB 双校验）
```

## 环境准备

```bash
python -m venv .venv
.venv\Scripts\activate                 # Windows
pip install -r requirements.txt
```

## 运行测试

```bash
# ===== prod：外网 JSONPlaceholder（默认），23 条，约 30~40s =====
pytest                                 # 自动跳过 local 用例
pytest tests/test_posts.py             # 只跑文章模块
pytest -k not_found                    # 按用例 ID 关键字筛选

# ===== dev：本地 FastAPI 服务，25 条，约 4s，无需手动启动服务 =====
pytest --env=dev                       # 框架自动拉起 uvicorn，跑完自动关闭
pytest --env=dev -k 403                # 只跑越权相关用例

pytest --collect-only                  # 查看用例清单（共 48 条，按环境自动分流）
```

> 也可以手动启动服务后再跑（框架检测到 8000 端口已占用会直接复用）：
> `uvicorn app.main:app --reload`，接口文档见 http://127.0.0.1:8000/docs

### 生成测试报告

```bash
# pytest-html 单文件报告
pytest --html=tests/reports/test_report.html --self-contained-html

# Allure 报告（需 Allure 命令行 + Java）
pytest --alluredir=tests/reports/allure --clean-alluredir
allure serve tests/reports/allure
```

## 本地被测服务接口

| 方法 & 路径 | 鉴权 | 说明 / 关键状态码 |
| --- | --- | --- |
| POST `/auth/register` | 无 | 注册，201；用户名重复 409；参数非法 422 |
| POST `/auth/login` | 无 | 登录返回 JWT，200；账号密码错误 401 |
| GET `/users/me` | 需登录 | 当前用户信息；无/伪造 token 返回 401 |
| GET `/posts` `/posts/{id}` | 无 | 列表（分页/作者过滤）、详情；不存在 404 |
| POST `/posts` | 需登录 | 创建，作者固定为当前用户，201；未登录 401 |
| PUT `/posts/{id}` | 需登录且为作者 | 整体更新；非作者 403、不存在 404、非法 422 |
| DELETE `/posts/{id}` | 需登录且为作者 | 删除；非作者 403、不存在 404 |

种子账号：`demo / Demo1234!`（拥有文章 id=1、2）。服务每次启动重建表并灌入种子数据，保证测试可重复。

## 用例设计概览（共 48 条）

| 套件 | 环境 | 数量 | 覆盖设计点 |
| --- | --- | --- | --- |
| test_posts / test_users | prod | 23 | CRUD、过滤、分页、ID 边界（0/负数/非数字/越界）、404、空列表、删除幂等 |
| test_auth_api | dev | 10 | 注册成功/重复/参数校验、登录成功/失败、JWT 有效/缺失/伪造、密码哈希落库 |
| test_posts_local | dev | 15 | 文章 CRUD 全链路、401/403/404/422、越权防护、分页过滤、**响应+DB 双校验** |

## 框架设计说明

- **双被测对象 + 自动分流**：`pytest_collection_modifyitems` 根据 `--env` 与 `local` 标记自动选择用例；
  dev 环境由 session 级 fixture 自动拉起/关闭 uvicorn 子进程，并轮询 `/health` 等待就绪。
- **响应 + 数据库双校验**：写接口不仅断言 HTTP 响应，还用 `DBInspector` 直连 SQLite 验证数据真正落库、
  字段一致；对 401/403/422 等被拦截场景，反向断言库中记录数不变，证明"没写错数据"。
- **鉴权透传**：`HttpClient.set_token` 统一注入 `Authorization: Bearer <token>`；`auth_client`
  fixture 自动完成注册→登录→带 token，`demo_client` 提供种子用户身份用于越权测试。
- **数据驱动与代码编排互补**：无状态的外网接口用 YAML 数据驱动；有登录态、动态数据、跨步骤链路的
  业务流用代码式 fixture 编排——这也是真实项目中的常见组合。
- **稳定性保障**：连接/读取双超时，仅对网络异常自动重试 2 次，业务断言失败不重试。
