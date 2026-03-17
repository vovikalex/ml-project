import os
import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
from fastapi import FastAPI, HTTPException, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import create_engine
from schema import UserGet, PostGet, FeedGet
from table_user import User
from table_post import Post
from table_feed import Feed
from database import SessionLocal
from typing import List, Optional
from datetime import datetime
from loguru import logger


def get_model_path(path: str) -> str:
    if os.environ.get("IS_LMS") == "1":  # проверяем где выполняется код в лмс, или локально.
        MODEL_PATH = '/workdir/user_input/model'
    else:
        MODEL_PATH = path
    return MODEL_PATH

def load_models():
    model_path = get_model_path('./catboost_model')
    try:
        model = CatBoostClassifier()
        model.load_model(model_path)
        return model
    except Exception:
        logger.exception("Ошибка загрузки модели")
        raise

def load_features() -> pd.DataFrame:
    logger.info("Загружаем посты с лайком юзера")
    query = """SELECT distinct post_id, user_id
            FROM public.feed_data where action = 'like'"""
    liked_posts = batch_load_sql(query)

    logger.info("Загружаем фичи по постам")
    query = """SELECT * from vl_aleksandrov_posts_info_features"""
    post_features = batch_load_sql(query)

    logger.info("Загружаем фичи по юзерам")
    query = """SELECT * from public.user_data"""
    user_features = batch_load_sql(query)

    return [liked_posts, post_features, user_features]


# Глобальные состояния, инициализируются на startup
model = None
features = None
model_loaded = False
features_loaded = False


def batch_load_sql(query: str) -> pd.DataFrame:
    CHUNKSIZE = 200000
    engine = create_engine(
        "postgresql://robot-startml-ro:pheiph0hahj1Vaif@"
        "postgres.lab.karpov.courses:6432/startml"
    )
    conn = engine.connect().execution_options(stream_results=True)
    try:
        chunks = []
        for chunk_dataframe in pd.read_sql(query, conn, chunksize=CHUNKSIZE):
            chunks.append(chunk_dataframe)
        if not chunks:
            # Возвращаем пустой DataFrame, если запрос не вернул строк
            return pd.DataFrame()
        return pd.concat(chunks, ignore_index=True)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        try:
            engine.dispose()
        except Exception:
            pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
def get_recommended_posts(
        user_id: int,
        time: datetime,
        limit: int = 10) -> List[PostGet]:

    logger.info(f"user_id:{user_id}")
    logger.info("считаем фичи")

    # Проверки наличия глобальных артефактов
    if features is None or not isinstance(features, (list, tuple)) or len(features) < 3:
        raise HTTPException(status_code=503, detail="Фичи не загружены")
    if model is None:
        raise HTTPException(status_code=503, detail="Модель не загружена")

    # Загружаем фичи по юзеру
    user_features = features[2].loc[features[2].user_id == user_id]
    if user_features.empty:
        logger.warning("Нет фич для user_id %s", user_id)
        return []
    user_features = user_features.drop('user_id', axis=1)

    # Загружаем фичи по постам
    post_features = features[1].drop(['index', 'text'], axis=1)
    content = features[1][['post_id', 'text', 'topic']]

    # Объединяем эти фичи
    logger.info("Всё соединим")
    add_user_features = dict(zip(user_features.columns, user_features.values[0]))
    user_post_features = post_features.assign(**add_user_features)
    user_post_features = user_post_features.set_index('post_id')

    # Добавляем инфо о дате рекоммендации
    logger.info('Добавляем инфо о дате')
    user_post_features['hour'] = time.hour
    user_post_features['month'] = time.month

    
    logger.info('Предсказываем')
    if user_post_features.empty:
        return []
    predicts = model.predict_proba(user_post_features)[:, 1]
    user_post_features['predicts'] = predicts

    logger.info('Убираем записи, которые уже лайкнуты')
    liked_posts = features[0]
    liked_posts = liked_posts[liked_posts.user_id == user_id].post_id.values
    filtered_ = user_post_features[~user_post_features.index.isin(liked_posts)]
    logger.info(f"Рекомендуем топ {limit} по вероятности")
    if filtered_.empty:
        return []
    posts = filtered_.sort_values('predicts')[-limit:].index

    results = []
    for i in posts:
        row = content[content.post_id == i]
        text = row.text.values[0] if not row.empty else ""
        topic = row.topic.values[0] if not row.empty else ""
        results.append(PostGet(**{'id': i, 'text': text, 'topic': topic}))
    return results
    
app = FastAPI()
@app.on_event("startup")
def startup_event():
    global model, features, model_loaded, features_loaded
    logger.info("Startup: загрузка модели и фич")
    try:
        model = load_models()
        model_loaded = True
        logger.info("Модель загружена")
    except Exception:
        model_loaded = False
        logger.exception("Ошибка загрузки модели: Startup")

    try:
        features = load_features()
        features_loaded = True
        logger.info("Фичи загружены")
    except Exception:
        features_loaded = False
        logger.exception("Ошибка загрузки фич: Startup")

    logger.info("Сервис поднят и работает")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Health check: сообщает состояния модели, фич и БД."""
    db_ok = True
    try:
        # простая проверка соединения
        db.execute(func.now())
    except Exception:
        db_ok = False
    return {"модель": model_loaded, "фичи": features_loaded, "бд": db_ok}


@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Ошибка БД: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ошибка БД"},
    )


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Непредвиденная ошибка: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "внутренняя ошибка сервера"},
    )


@app.get("/user/{user_id}", response_model=UserGet)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserGet:
    """Вернуть информацию о пользователе по `user_id`.

    Возвращает `UserGet` или 404, если пользователь не найден.
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
    return db.query(Feed).filter(Feed.user_id == user_id).order_by(Feed.time.desc()).limit(limit).all()

@app.get("/post/{post_id}/feed", response_model=List[FeedGet])
def get_feed_post(post_id: int, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Вернуть последние записи ленты для поста `post_id`.

    Параметр `limit` ограничивает количество возвращаемых записей (по умолчанию 10).
    """
    return db.query(Feed).filter(Feed.post_id == post_id).order_by(Feed.time.desc()).limit(limit).all()

@app.get("/post/recommendations/", response_model=List[PostGet])
def get_recommendations(user_id: int, time: Optional[datetime] = None, limit: int = Query(10, ge=1, le=100)) -> List[PostGet]:
    """Получить рекомендованные посты для пользователя `user_id` на момент `time`.

    Если `time` не указан, используется текущее время сервера.
    Возвращает список `PostGet` длиной до `limit` упорядоченных по вероятности лайка.
    """
    if time is None:
        time = datetime.utcnow()
    return get_recommended_posts(user_id, time, limit)
   
@app.get("/")
def hello():
    """Простой роут проверки доступности сервиса."""
    return "Привет!"