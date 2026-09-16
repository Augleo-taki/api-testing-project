# api-testing-project

基于 **Python + pytest + requests** 的分层接口自动化测试项目，包含两个被测对象：

1. **公开练习 API** [JSONPlaceholder](https://jsonplaceholder.typicode.com/)（prod 环境）：
   用 **YAML 数据驱动**测试 users / posts，结合等价类、边界值设计正/负向用例，JSON Schema 校验响应。
2. **自建被测服务**（dev 环境）：用 **FastAPI + SQLite + JWT** 实现的博客后端，覆盖注册登录、
   令牌鉴权、文章 CRUD、越权防护，并做**响应断言 + 数据库断言双校验**；测试时框架自动启停服务，
   本地秒级跑完，摆脱对外网的依赖。

此外用 **responses / pytest-mock** 做 HTTP 协议层与函数层打桩、用**纯单元测试**覆盖安全模块；
配置 **GitHub Actions** 在推送时自动跑测试，并提供 **Docker / Docker Compose** 一键启动被测服务。
两套用例通过 `local` 标记 + `--env` 参数**自动分流**，共 63 条用例（prod 38 / dev 40）。

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
| Mock 打桩 | responses 0.26.3（HTTP 协议层）、pytest-mock 3.15.1（函数层） |
| 持续集成 | GitHub Actions（推送自动跑两套测试，留存 Allure 产物） |
| 容器化 | Docker + Docker Compose（一键启动被测服务） |
| 测试报告 | Allure（allure-pytest 2.16.0）、pytest-html 4.2.0 |
| 失败重试 | pytest-rerunfailures 16.6.1（仅网络异常重试，断言失败不重试） |

## 目录结构

```text
api-testing-project/
├── .github/workflows/test.yml # 【2-B】CI：推送自动跑测试
├── Dockerfile                # 【2-B】被测服务镜像
├── docker-compose.yml        # 【2-B】一键启动被测服务
├── .dockerignore
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
    ├── test_posts_local.py                  # dev 文章 15 条（含 DB 双校验）
    ├── test_mock_http.py                    # 【2-B】responses HTTP 打桩 5 条
    └── test_security_unit.py                # 【2-B】安全模块单元测试 10 条
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
pytest --env=dev                       # 框架自动拉起 uvicorn，跑完自动关闭（含 mock/unit）
pytest --env=dev -k 403                # 只跑越权相关用例

# ===== Mock 与单元测试（不依赖任何服务/网络，任意环境都可单独跑）=====
pytest -m "mock or unit"               # 5 条 HTTP 打桩 + 10 条安全模块单测

pytest --collect-only                  # 查看用例清单（共 63 条，按环境/marker 自动分流）
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

## 用例设计概览（共 63 条）

| 套件 | 标记 / 环境 | 数量 | 覆盖设计点 |
| --- | --- | --- | --- |
| test_posts / test_users | prod（YAML 驱动） | 23 | CRUD、过滤、分页、ID 边界（0/负数/非数字/越界）、404、空列表、删除幂等 |
| test_auth_api | local / dev | 10 | 注册成功/重复/参数校验、登录成功/失败、JWT 有效/缺失/伪造、密码哈希落库 |
| test_posts_local | local / dev | 15 | 文章 CRUD 全链路、401/403/404/422、越权防护、分页过滤、**响应+DB 双校验** |
| test_mock_http | mock（任意环境） | 5 | responses 打桩 200/500/读超时/断连/瞬时故障恢复，确定性构造异常 |
| test_security_unit | unit（任意环境） | 10 | PBKDF2 哈希校验、JWT 往返/篡改/伪造/过期（mocker 打桩）等纯函数单测 |

## Mock 打桩说明

- **什么时候用 Mock**：真实环境难以稳定复现的异常（500、超时、断连）、尚未开发完成的下游、
  不希望测试依赖网络时。原则：**被测对象自身的逻辑不 mock，只 mock 它的外部依赖**。
- **两种粒度**：
  - `responses`（HTTP 协议层，见 `tests/test_mock_http.py`）：在 requests 发请求前拦截，
    不打开发出的请求，最贴近真实网络行为，可用 `responses.calls` 断言调用次数；
  - `pytest-mock` 的 `mocker.patch`（Python 函数层，见 `tests/test_security_unit.py`）：
    直接替换函数/常量，例如把令牌有效期改成负数，零成本复现"令牌过期"。
- **进程边界**：`responses`/`mocker` 只能影响测试进程自身；独立 uvicorn 子进程内部的下游调用
  无法被这样打桩，那种场景通常配合 FastAPI 的依赖注入或 TestClient 在同进程测试。

## 持续集成（GitHub Actions）

`.github/workflows/test.yml` 在每次 push / Pull Request 到 `main` 时自动：

1. 在 ubuntu-latest 上准备 Python 3.13 并安装依赖；
2. 运行 `pytest --env=dev`（本地服务用例 + Mock + 单测，框架自动启停 uvicorn）；
3. 运行外网用例 `pytest -m "not local and not mock and not unit"`；
4. 上传 Allure 原始结果为构建产物（Artifact）。

在仓库的 **Actions** 标签页可查看每次运行的结果与日志。

## Docker 一键启动被测服务

```bash
docker compose up -d --build          # 构建并后台启动服务（映射到本机 8000 端口）
docker compose ps                     # 查看状态与健康检查
# 服务就绪后，在宿主机跑本地用例（框架检测到端口被占用会复用容器服务）：
pytest --env=dev
docker compose down                   # 停止并移除容器
```

> 说明：当前镜像只打包被测服务（`app/`），测试在宿主机运行；测试框架的"端口已占用则复用"
> 设计正好用于对接容器。生产级做法可再增加一个测试镜像，在 Compose 网络内用服务名通信。

## 框架设计说明

- **双被测对象 + 自动分流**：`pytest_collection_modifyitems` 根据 `--env` 与 `local` 标记自动选择用例；
  dev 环境由 session 级 fixture 自动拉起/关闭 uvicorn 子进程，并轮询 `/health` 等待就绪。
- **响应 + 数据库双校验**：写接口不仅断言 HTTP 响应，还用 `DBInspector` 直连 SQLite 验证数据真正落库、
  字段一致；对 401/403/422 等被拦截场景，反向断言库中记录数不变，证明"没写错数据"。
- **鉴权透传**：`HttpClient.set_token` 统一注入 `Authorization: Bearer <token>`；`auth_client`
  fixture 自动完成注册→登录→带 token，`demo_client` 提供种子用户身份用于越权测试。
- **数据驱动与代码编排互补**：无状态的外网接口用 YAML 数据驱动；有登录态、动态数据、跨步骤链路的
  业务流用代码式 fixture 编排——这也是真实项目中的常见组合。
- **测试分层**：接口测试（真实 HTTP + DB 断言）为主，纯单元测试（安全函数）保证快速精确定位，
  Mock 用例负责稳定构造异常场景，三者构成测试金字塔的不同层级。
- **CI / 容器化**：GitHub Actions 推送即回归；Docker Compose 让任何人无需配置本地环境即可起服务。
- **稳定性保障**：连接/读取双超时，仅对网络异常自动重试 2 次，业务断言失败不重试。
