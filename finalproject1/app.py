from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from schema import UserGet, PostGet, FeedGet
from table_user import User
from table_post import Post
from table_feed import Feed
from database import SessionLocal
from typing import List
from loguru import logger

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/user/{user_id}", response_model=UserGet)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserGet:
    """Вернуть информацию о юзере по `user_id`.

    Возвращает `UserGet` или 404, если юзер не найден.
    """
    result = db.query(User).filter(User.id == user_id).one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="юзер не найден")
    return result


@app.get("/post/{post_id}", response_model=PostGet)
def get_post(post_id: int, db: Session = Depends(get_db)) -> PostGet:
    """Вернуть информацию о посте по `post_id`.

    Возвращает `PostGet` или 404, если пост не найден.
    """
    result = db.query(Post).filter(Post.id == post_id).one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="пост не найден")
    return result


@app.get("/user/{user_id}/feed", response_model=List[FeedGet])
def get_feed_user(user_id: int, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Вернуть последние записи ленты для пользователя `user_id`.

    Параметр `limit` ограничивает количество возвращаемых записей (по умолчанию 10).
    """
    return (
        db.query(Feed)
        .filter(Feed.user_id == user_id)
        .order_by(Feed.time.desc())
        .limit(limit)
        .all()
    )


@app.get("/post/{post_id}/feed", response_model=List[FeedGet])
def get_feed_post(post_id: int, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Вернуть последние записи ленты для поста `post_id`.

    Параметр `limit` ограничивает количество возвращаемых записей (по умолчанию 10).
    """
    return (
        db.query(Feed)
        .filter(Feed.post_id == post_id)
        .order_by(Feed.time.desc())
        .limit(limit)
        .all()
    )


@app.get("/post/recommendations/", response_model=List[PostGet])
def get_recomendations(user_id: int = 0, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Получить рекомендованные посты.

    Если `user_id` указан (не 0), рекомендации будут с учетом действий этого пользователя.
    Возвращает список `PostGet`, упорядоченный по популярности (числу лайков).
    """
    q = (
        db.query(Post)
        .select_from(Feed)
        .filter(Feed.action == "like")
        .join(Post)
        .group_by(Post.id)
        .order_by(func.count(Post.id).desc())
    )
    if user_id:
        q = q.filter(Feed.user_id == user_id)
    return q.limit(limit).all()


@app.get("/")
def hello():
    """Простой роут проверки доступности сервиса."""
    return "Привет!"
