from sqlalchemy import select, delete, update

from app.database.engine import engine, session_maker
from app.database.models import Base
from app.database.models import Channel, User, Account


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def orm_add_user(tg_id: int, name: str):
    async with session_maker() as session:
        async with session.begin():
            obj = User(tg_id=tg_id, name=name)
            session.add(obj)
            await session.commit()
            return obj


async def orm_add_user_by_name(name: str):
    async with session_maker() as session:
        async with session.begin():
            obj = User(name=name)
            session.add(obj)
            await session.commit()
            return obj


async def orm_remove_user(name: str):
    async with session_maker() as session:
        async with session.begin():
            query = delete(User).where(User.name == name)
            await session.execute(query)
            await session.commit()


async def orm_get_user(tg_id: int):
    async with session_maker() as session:
        async with session.begin():
            query = select(User).where(User.tg_id == tg_id)
            result = await session.execute(query)
            return result.scalar()


async def orm_get_users():
    async with session_maker() as session:
        async with session.begin():
            query = select(User)
            result = await session.execute(query)
            return result.scalars().all()


async def orm_is_admin(tg_id: int):
    async with session_maker() as session:
        async with session.begin():
            query = select(User).where(User.tg_id == tg_id)
            result = await session.execute(query)
            user = result.scalar()
            return user.is_admin if user else False


async def add_admin(tg_id: int):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = update(User).where(User.tg_id == tg_id).values(is_admin=True)
                await session.execute(query)
                await session.commit()
                return True
    except:
        return False


async def remove_admin(tg_id: int):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = update(User).where(User.tg_id == tg_id).values(is_admin=False)
                await session.execute(query)
                await session.commit()
                return True
    except:
        return False


async def get_all_admins():
    async with session_maker() as session:
        async with session.begin():
            query = select(User).where(User.is_admin == True)
            result = await session.execute(query)
            admins = result.scalars().all()
            return admins


async def orm_add_channel(chat: str, phone_number: str, status: bool):
    async with session_maker() as session:
        async with session.begin():
            account = await orm_get_account(phone_number)

            obj = Channel(chat=chat, status=status, account_id=account.id)
            session.add(obj)
            await session.commit()
            return obj


async def orm_channel_processed(chat: str) -> bool:
    async with session_maker() as session:
        async with session.begin():
            query = select(Channel).where(Channel.chat == chat)
            result = await session.execute(query)
            return result.scalar() is not None


async def orm_remove_channels():
    async with session_maker() as session:
        async with session.begin():
            query = delete(Channel)
            await session.execute(query)
            await session.commit()

async def orm_add_account(phone_number: str, api_id: str, api_hash: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                obj = Account(phone_number=phone_number, api_id=api_id, api_hash=api_hash)
                session.add(obj)

                await session.commit()
                return obj
    except:
        return False


async def orm_remove_account(phone_number: str):
    async with session_maker() as session:
        async with session.begin():
            query = delete(Account).where(Account.phone_number == phone_number)
            await session.execute(query)
            await session.commit()


async def orm_get_accounts():
    async with session_maker() as session:
        async with session.begin():
            query = select(Account)
            result = await session.execute(query)
            return result.scalars().all()


async def orm_get_account(phone_number: str):
    async with session_maker() as session:
        async with session.begin():
            query = select(Account).where(Account.phone_number == phone_number)
            result = await session.execute(query)
            return result.scalar()


async def orm_is_account_active(phone_number: str):
    async with session_maker() as session:
        async with session.begin():
            query = select(Account).where(Account.phone_number == phone_number)
            result = await session.execute(query)
            return result.scalar().is_active

async def orm_set_account_active(phone_number: str, status: bool):
    async with session_maker() as session:
        async with session.begin():
            query = select(Account).where(Account.phone_number == phone_number)
            result = await session.execute(query)
            account = result.scalar()
            if account:
                account.is_active = status
                await session.commit()
                return True
            return False

async def orm_check_active_type(phone_number: str):
    async with session_maker() as session:
        async with session.begin():
            query = select(Account).where(Account.phone_number == phone_number)
            result = await session.execute(query)
            return result.scalar().active_type

async def orm_update_active_type(phone_number: str, active_type: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = update(Account).where(Account.phone_number == phone_number).values(active_type=active_type)
                await session.execute(query)
                await session.commit()
                return True
    except:
        return False