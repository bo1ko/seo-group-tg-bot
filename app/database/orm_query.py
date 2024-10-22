from sqlalchemy import select

from app.database.engine import get_session
from app.database.models import User, Base


def create_tables():
    Base.metadata.create_all(bind=get_session().bind)


# Add user to User table
def orm_add_user(tg_id: int, name: str):
    with get_session() as session:
        obj = User(
            tg_id=tg_id,
            name=name,
        )
        session.add(obj)
        result = session.execute()

    return result


# Get user from User table
def orm_get_user(tg_id: int):
    with get_session() as session:
        query = select(User).where(User.tg_id == tg_id)
        result = session.execute(query)

    return result.scalar()


# Check admin status
def orm_is_admin(tg_id: int):
    with get_session() as session:
        query = select(User).where(User.tg_id == tg_id)
        result = session.execute(query).scalar()

        return result.is_admin if result else False
