# -*- coding: utf-8 -*-
"""初始化并灌入种子数据。

被测服务每次启动都重建表并写入固定种子数据，保证测试可重复、幂等；
这是"测试专用被测服务"的常见做法，生产服务不会每次启动清库。
"""

from app.database import Base, SessionLocal, engine
from app.models import Post, User
from app.security import hash_password

# 固定种子账号，测试与文档都可直接使用
SEED_USERNAME = "demo"
SEED_PASSWORD = "Demo1234!"


def reset_and_seed() -> None:
    """删表重建并写入 1 个种子用户 + 2 篇文章。"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        demo = User(username=SEED_USERNAME, password_hash=hash_password(SEED_PASSWORD))
        db.add(demo)
        db.flush()  # 拿到 demo.id

        db.add_all(
            [
                Post(
                    title="第一篇博客",
                    body="这是种子数据：欢迎使用接口测试练习服务。",
                    author_id=demo.id,
                ),
                Post(
                    title="第二篇博客",
                    body="登录后可以创建、修改、删除自己的文章。",
                    author_id=demo.id,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()
