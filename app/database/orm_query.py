from sqlalchemy import select, delete

from app.database.engine import get_session
from app.database.models import Channel, User, Base


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
        session.commit()

        return obj


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

# Add a channel to the channels table
def orm_add_channel(chat: str, status: bool):
    with get_session() as session:
        obj = Channel(
            chat=chat,
            status=status,
        )
        session.add(obj)
        session.commit()

        return obj


# Check if a channel has been processed
def orm_channel_processed(chat: str) -> bool:
    with get_session() as session:
        query = select(Channel).where(Channel.chat == chat)
        result = session.execute(query).scalar()

        return result is not None

def orm_remove_channels():
    with get_session() as session:
        query = delete(Channel)
        session.execute(query)
