# -*- coding: utf-8 -*-
"""数据库引擎与会话（SQLAlchemy 2.0 + SQLite）。"""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 数据库文件放在项目根目录，测试框架的 DB 断言连同一个文件
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "test_app.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# SQLite 默认不开启外键约束，显式打开
@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI 依赖：每个请求一个数据库会话，请求结束关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
