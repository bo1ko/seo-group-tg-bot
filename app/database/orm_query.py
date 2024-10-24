from pyrogram.raw import objects
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import engine
from app.database.models import Base
from app.database.models import Channel, User, Keyword


async def create_tables(session: AsyncSession):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def orm_add_user(tg_id: int, name: str, session: AsyncSession):
    async with session:
        obj = User(tg_id=tg_id, name=name)
        session.add(obj)
        await session.commit()
        return obj

async def orm_add_user_by_name(name: str, session: AsyncSession):
    async with session:
        obj = User(name=name)
        session.add(obj)
        await session.commit()
        return obj

async def orm_remove_user(name: str, session: AsyncSession):
    async with session:
        query = delete(User).where(User.name == name)
        await session.execute(query)
        await session.commit()

async def orm_get_user(tg_id: int, session: AsyncSession):
    async with session:
        query = select(User).where(User.tg_id == tg_id)
        result = await session.execute(query)
        return result.scalar()

async def orm_get_users(session: AsyncSession):
    async with session:
        query = select(User)
        result = await session.execute(query)
        return result.scalars().all()


async def orm_is_admin(tg_id: int, session: AsyncSession):
    async with session:
        query = select(User).where(User.tg_id == tg_id)
        result = await session.execute(query)
        user = result.scalar()
        return user.is_admin if user else False

async def add_admin(tg_id: int, session: AsyncSession):
    try:
        async with session:
            query = update(User).where(User.tg_id == tg_id).values(is_admin=True)
            await session.execute(query)
            await session.commit()
            return True
    except:
        return False

async def remove_admin(tg_id: int, session: AsyncSession):
    try:
        async with session:
            query = update(User).where(User.tg_id == tg_id).values(is_admin=False)
            await session.execute(query)
            await session.commit()
            return True
    except:
        return False

async def get_all_admins(session: AsyncSession):
    async with session:
        query = select(User).where(User.is_admin == True)
        result = await session.execute(query)
        admins = result.scalars().all()
        return admins



async def orm_add_channel(chat: str, status: bool, session: AsyncSession):
    async with session:
        obj = Channel(chat=chat, status=status)
        session.add(obj)
        await session.commit()
        return obj


async def orm_channel_processed(chat: str, session: AsyncSession) -> bool:
    async with session:
        query = select(Channel).where(Channel.chat == chat)
        result = await session.execute(query)
        return result.scalar() is not None


async def orm_remove_channels(session: AsyncSession):
    async with session:
        query = delete(Channel)
        await session.execute(query)
        await session.commit()


async def orm_add_keywords(words: list[str], session: AsyncSession):
    async with session:
        objects = [Keyword(word=word) for word in words]
        session.add_all(objects)
        await session.commit()
        return objects


async def orm_get_keywords(session: AsyncSession):
    async with session:
        query = select(Keyword)
        result = await session.execute(query)
        return result.scalars().all()


async def orm_remove_keywords(keywords: list[str], session: AsyncSession):
    async with session:
        query = delete(Keyword).where(Keyword.word.in_(keywords))
        await session.execute(query)
        await session.commit()
