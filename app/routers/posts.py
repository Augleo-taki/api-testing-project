# -*- coding: utf-8 -*-
"""文章接口：列表/详情公开，增改删需登录且只能操作自己的文章。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Post, User
from app.schemas import PostCreate, PostOut, PostUpdate

router = APIRouter(tags=["文章"])


def _get_post_or_404(post_id: int, db: Session) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    return post


@router.get("/posts", response_model=list[PostOut])
def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    author_id: int | None = None,
    db: Session = Depends(get_db),
):
    """文章列表，支持分页（skip/limit）与按作者过滤。"""
    stmt = select(Post).order_by(Post.id)
    if author_id is not None:
        stmt = stmt.where(Post.author_id == author_id)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt))


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """文章详情，不存在返回 404。"""
    return _get_post_or_404(post_id, db)


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建文章（需登录），作者固定为当前用户。"""
    post = Post(
        title=payload.title,
        body=payload.body,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/posts/{post_id}", response_model=PostOut)
def update_post(
    post_id: int,
    payload: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """整体更新文章（需登录）；非作者返回 403。"""
    post = _get_post_or_404(post_id, db)
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改他人文章")

    post.title = payload.title
    post.body = payload.body
    db.commit()
    db.refresh(post)
    return post


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除文章（需登录）；非作者返回 403。"""
    post = _get_post_or_404(post_id, db)
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除他人文章")

    db.delete(post)
    db.commit()
    return {"message": "文章已删除", "id": post_id}
