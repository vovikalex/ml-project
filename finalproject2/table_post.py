from database import Base, SessionLocal
from sqlalchemy import Column, Integer, String, Text


class Post(Base):
    """ORM-модель поста."""

    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    topic = Column(String, nullable=True)

    def __repr__(self):
        return f"<Post id={self.id} topic={self.topic}>"


if __name__ == "__main__":
    session = SessionLocal()
    try:
        results = (
            session.query(Post.id)
            .filter(Post.topic == "business")
            .order_by(Post.id.desc())
            .limit(10)
            .all()
        )
        print([row[0] for row in results])
    finally:
        session.close()
