from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class BaseSchema(BaseModel):
    """Базовая Pydantic схема с включённым режимом ORM."""

    class Config:
        orm_mode = True


class UserGet(BaseSchema):
    """Схема ответа для пользователя."""

    id: int = Field(..., description="ID пользователя", example=123)
    gender: int = Field(..., description="Пол (код) пользователя", example=1)
    age: int = Field(..., description="Возраст пользователя", example=31)
    country: str = Field(..., description="Страна", example="Russia")
    city: str = Field(..., description="Город", example="Moscow")
    exp_group: int = Field(..., description="Экспериментальная группа", example=2)
    os: str = Field(..., description="Операционная система пользователя", example="Android")
    source: str = Field(..., description="Источник трафика/реферал", example="organic")


class PostGet(BaseSchema):
    """Схема ответа для поста (упрощённая версия)."""

    id: int = Field(..., description="ID поста", example=10)
    text: str = Field(..., description="Текст поста", example="Короткий текст поста")
    topic: Optional[str] = Field(None, description="Тема поста (может быть пустой)", example="business")


class FeedGet(BaseSchema):
    """Схема ответа для записи ленты (feed action).

    По умолчанию вложенные объекты `user` и `post` делаются опциональными,
    чтобы ответы не перегружались при массовых запросах.
    """

    user_id: int = Field(..., description="ID пользователя", example=123)
    post_id: int = Field(..., description="ID поста", example=10)
    user: Optional[UserGet] = Field(None, description="Информация о пользователе", example={"id": 123, "gender": 1, "age": 31, "country": "Russia", "city": "Moscow", "exp_group": 2, "os": "Android", "source": "organic"})
    post: Optional[PostGet] = Field(None, description="Информация о посте", example={"id": 10, "text": "Короткий текст поста", "topic": "business"})
    action: Literal["view", "like"] = Field(..., description="Тип действия пользователя над постом", example="view")
    time: datetime = Field(..., description="Время события в формате ISO 8601", example="2021-12-15T12:34:56Z")
