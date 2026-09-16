# -*- coding: utf-8 -*-
"""数据库断言工具（DB Inspector）。

作用：接口测试不能只校验 HTTP 响应，还要连数据库确认数据真正落库、
且字段值正确——这就是"响应断言 + DB 断言"双校验。

测试框架用独立连接只读查询被测服务写入的同一个 SQLite 文件，
与服务自身的连接互不影响。
"""

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database import DATABASE_URL
from app.models import Post, User

__all__ = ["DBInspector", "User", "Post"]


class DBInspector:
    """对被测库提供只读的计数 / 查询能力。"""

    def __init__(self, db_url: str | None = None):
        # check_same_thread=False：允许在 fixture/用例线程中使用
        self.engine = create_engine(
            db_url or DATABASE_URL,
            connect_args={"check_same_thread": False},
        )

    def count(self, model, **filters) -> int:
        """统计记录数，可带等值过滤，如 count(Post, author_id=2)。"""
        with Session(self.engine) as db:
            stmt = select(func.count()).select_from(model)
            if filters:
                stmt = stmt.filter_by(**filters)
            return int(db.scalar(stmt))

    def exists(self, model, **filters) -> bool:
        return self.count(model, **filters) > 0

    def get(self, model, **filters) -> dict | None:
        """按等值条件查单条，返回列名->值的字典；查不到返回 None。"""
        with Session(self.engine) as db:
            obj = db.scalar(select(model).filter_by(**filters))
            if obj is None:
                return None
            return {
                column.name: getattr(obj, column.name)
                for column in model.__table__.columns
            }

    def close(self) -> None:
        self.engine.dispose()
