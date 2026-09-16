# -*- coding: utf-8 -*-
"""被测服务（SUT）：基于 FastAPI + SQLite + JWT 的简易博客后端。

该包是"被测对象"，与 tests/ 测试框架代码分离：
    app/      被测服务（启动命令：uvicorn app.main:app）
    tests/    自动化测试
"""
