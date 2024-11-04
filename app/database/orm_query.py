from datetime import datetime

from sqlalchemy import select, delete, update, distinct

from app.database.engine import engine, session_maker
from app.database.models import Base
from app.database.models import Channel, User, Account, Subscription


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def orm_add_user(tg_id: str, name: str):
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


async def orm_get_user(tg_id: str):
        async with session_maker() as session:
            async with session.begin():
                try:
                    query = select(User).where(User.tg_id == tg_id)
                    result = await session.execute(query)
                    return result.scalar()
                except:
                    return None


async def orm_get_users():
    async with session_maker() as session:
        async with session.begin():
            query = select(User)
            result = await session.execute(query)
            return result.scalars().all()


async def orm_is_admin(tg_id: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = select(User).where(User.tg_id == tg_id)
                result = await session.execute(query)
                user = result.scalar()
                return user.is_admin
    except:
        return False


async def add_admin(tg_id: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = update(User).where(User.tg_id == tg_id).values(is_admin=True)
                await session.execute(query)
                await session.commit()
                return True
    except:
        return False


async def remove_admin(tg_id: str):
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


async def orm_get_channel_data(chat_name: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = select(Channel).where(Channel.chat == chat_name)
                result = await session.execute(query)
                channel = result.scalar()
                
                return f'{channel.country} {channel.city} {channel.is_general}'
    except Exception as e:
        print(e)
        return False

async def orm_add_channel(chat: str, phone_number: str, status: bool, country: str, city: str, is_general: bool):
    async with session_maker() as session:
        async with session.begin():
            account = await orm_get_account(phone_number)

            obj = Channel(chat=chat, status=status, account_id=account.id, country=country, city=city, is_general=is_general)
            session.add(obj)
            await session.commit()
            return obj


async def orm_channel_processed(chat: str):
    async with session_maker() as session:
        async with session.begin():
            query = (
                select(Channel, Account.phone_number)
                .join(Account)
                .where(Channel.chat == chat)
            )
            result = await session.execute(query)
            row = result.one_or_none()

            if row:
                channel, phone_number = row
                return channel, phone_number
            else:
                return None, None


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
                obj = Account(
                    phone_number=phone_number, api_id=api_id, api_hash=api_hash
                )
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

async def orm_disable_active_accounts():
    async with session_maker() as session:
        async with session.begin():
            query = select(Account)
            result = await session.execute(query)
            accounts = result.scalars().all()
            
            for account in accounts:
                if account.is_active:
                    account.is_active = False
                    await session.commit()


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
                query = (
                    update(Account)
                    .where(Account.phone_number == phone_number)
                    .values(active_type=active_type)
                )
                await session.execute(query)
                await session.commit()
                return True
    except:
        return False


async def orm_update_flood_wait(phone_number: str, flood_wait: datetime):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = (
                    update(Account)
                    .where(Account.phone_number == phone_number)
                    .values(flood_wait=flood_wait)
                )
                await session.execute(query)
                await session.commit()
                return True
    except:
        return False

########## Subscribe ##########
async def orm_get_subscribers():
    async with session_maker() as session:
        async with session.begin():
            query = select(Subscription)
            result = await session.execute(query)

            return result.scalars().all()


async def orm_get_subscriber(tg_id: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = select(Subscription).where(Subscription.user_id == tg_id)
                result = await session.execute(query)
                return result.scalar()
    except Exception as e:
        print(e)
        return False


async def orm_add_subscriber(tg_id: str, start_date: datetime, end_date: datetime):
    async with session_maker() as session:
        async with session.begin():
            obj = Subscription(
                user_id=tg_id,
                is_subscribed=True,
                start_subscription_date=start_date,
                end_subscription_date=end_date,
            )
            session.add(obj)

            await session.commit()
            return obj


async def orm_update_subscriber(tg_id: str, start_date: str, end_date: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = (
                    update(Subscription)
                    .where(Subscription.user_id == tg_id)
                    .values(
                        user_id=tg_id,
                        is_subscribed=True,
                        start_subscription_date=start_date,
                        end_subscription_date=end_date,
                    )
                )

                await session.execute(query)
                await session.commit()
                return True
    except:
        return False


async def orm_disable_all_subscriptions(tg_id: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = (
                    update(Subscription)
                    .where(Subscription.user_id == tg_id)
                    .values(is_subscribed=False)
                )
                await session.execute(query)
                await session.commit()
                return True
    except:
        return False

async def orm_disable_active_subscribers(tg_id: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = (
                    update(Subscription)
                    .where(Subscription.user_id == tg_id, Subscription.is_subscribed == True)
                    .values(is_subscribed=False)
                )
                await session.execute(query)
                await session.commit()
                return True
    except:
        return False


async def orm_is_sub_user(tg_id: str):
    async with session_maker() as session:
        async with session.begin():
            query = select(Subscription).where(Subscription.user_id == tg_id, Subscription.is_subscribed == True)
            result = await session.execute(query)
            sub_user = result.scalar()

            if sub_user:
                return sub_user.is_subscribed
            else:
                return False


### ORM KEYWORDS
async def orm_add_keywords(tg_id: str, keywords_list: list):
    try:
        async with session_maker() as session:
            async with session.begin():
                result = await session.execute(select(User).where(User.tg_id == tg_id))
                user = result.scalar()

                if user:
                    if user.key_list is None:
                        user.key_list = keywords_list
                    else:
                        user.key_list.extend(keywords_list)

                    await session.commit()
                    return True
                else:
                    return False
    except Exception as e:
        print(e)
        return False

async def orm_get_keywords(tg_id: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = select(User).where(User.tg_id == tg_id)
                result = await session.execute(query)
                user = result.scalar()

                return user.key_list
    except:
        return False


async def orm_remove_keywords(tg_id: str, keywords_to_remove: list):
    try:
        async with session_maker() as session:
            async with session.begin():
                query = select(User).where(User.tg_id == tg_id)
                result = await session.execute(query)
                user = result.scalar()

                if user and user.key_list:
                    user.key_list = [keyword for keyword in user.key_list if keyword not in keywords_to_remove]

                    await session.commit()
                    return True
                else:
                    return False
    except Exception as e:
        print(e)
        return False


async def get_unique_channels_data():
    try:
        async with session_maker() as session: 
            result = await session.execute(
                select(
                    Channel.country, 
                    Channel.city, 
                    Channel.is_general
                ).distinct()
            )
            return result.fetchall()
    except Exception as e:
        print(e)
        return False

async def orm_update_user_db(tg_id: str, new_db: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                # Retrieve the current db_list for the user
                result = await session.execute(
                    select(User).where(User.tg_id == tg_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    # Append the new element to the db_list
                    if user.db_list is None:
                        user.db_list = []  # Initialize if it's None
                    elif new_db not in user.db_list:
                        user.db_list.append(new_db)

                        # Update the user in the database
                        await session.execute(
                            update(User)
                            .where(User.tg_id == tg_id)
                            .values(db_list=user.db_list)
                        )
                        await session.commit()
                        return True
                    return False
                else:
                    return False  # User not found
    except Exception as e:
        print(f"Error occurred: {e}")
        return False

async def orm_remove_user_db(tg_id: str, db_to_remove: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                # Retrieve the current db_list for the user
                result = await session.execute(
                    select(User).where(User.tg_id == tg_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    # Remove the element from the db_list
                    print('!!!!!!!!!!!!', db_to_remove, user.db_list)
                    if user.db_list is not None and db_to_remove in user.db_list:
                        user.db_list.remove(db_to_remove)

                        # Update the user in the database
                        await session.execute(
                            update(User)
                            .where(User.tg_id == tg_id)
                            .values(db_list=user.db_list)
                        )
                        await session.commit()
                        return True
                    return False  # db_to_remove was not in the list
                else:
                    return False  # User not found
    except Exception as e:
        print(f"Error occurred: {e}")
        return False

async def orm_increment_message_count(tg_id: str):
    try:
        async with session_maker() as session:
            async with session.begin():
                # Retrieve the current message_count for the user
                result = await session.execute(
                    select(User).where(User.tg_id == tg_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    # Increment message_count by 1, initialize if None
                    user.message_count = (user.message_count or 0) + 1

                    # Update the user in the database
                    await session.execute(
                        update(User)
                        .where(User.tg_id == tg_id)
                        .values(message_count=user.message_count)
                    )
                    await session.commit()
                    return True
                else:
                    return False  # User not found
    except Exception as e:
        print(f"Error occurred: {e}")
        return False