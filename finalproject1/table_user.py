from database import Base, SessionLocal
from sqlalchemy import Column, Integer, String, select, func


class User(Base):
    """ORM-модель юзера."""

    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    gender = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    country = Column(String, nullable=False)
    city = Column(String, nullable=False)
    exp_group = Column(Integer, nullable=False)
    os = Column(String, nullable=False)
    source = Column(String, nullable=False)

    def __repr__(self):
        return f"<User id={self.id}>"


if __name__ == "__main__":
    session = SessionLocal()
    try:
        result = (
            select(User.country, User.os, func.count("*"))
            .filter(User.exp_group == 3)
            .group_by(User.country, User.os)
            .having(func.count("*") > 100)
            .order_by(func.count("*").desc())
        )
        print(session.execute(result).all())
    finally:
        session.close()
