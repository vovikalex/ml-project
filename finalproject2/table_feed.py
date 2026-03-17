from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.orm import relationship

from database import Base, SessionLocal
from table_post import Post
from table_user import User


class Feed(Base):
    """ORM-модель связей юзеров и постов."""

    __tablename__ = "feed_action"
    user_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    user = relationship(User)
    post_id = Column(Integer, ForeignKey(Post.id), primary_key=True)
    post = relationship(Post)
    action = Column(String, nullable=False)
    time = Column(DateTime, nullable=False, primary_key=True)

    def __repr__(self):
        return f"<Feed user_id={self.user_id} post_id={self.post_id} action={self.action} time={self.time}>"


if __name__ == "__main__":
    session = SessionLocal()
    try:
        stmt = select(Feed.action, User.id).join(User).join(Post)
        result = session.execute(stmt).fetchone()
        print(result)
    finally:
        session.close()
