from sqlalchemy import DateTime, String, func, Integer, Boolean, ForeignKey, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from sqlalchemy.ext.mutable import MutableList

class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class MutableArray(MutableList):
    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            value = MutableList(value)
        return super(MutableArray, cls).coerce(key, value)

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    message_count: Mapped[int] = mapped_column(Integer, nullable=True)
    db_list: Mapped[list[str]] = mapped_column(MutableArray.as_mutable(ARRAY(String)), nullable=True)
    key_list: Mapped[list[str]] = mapped_column(MutableArray.as_mutable(ARRAY(String)), nullable=True)

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey('users.tg_id', ondelete='CASCADE'))
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    start_subscription_date: Mapped[datetime] = mapped_column(DateTime)
    end_subscription_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

class Channel(Base):
    __tablename__ = 'channels'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[bool] = mapped_column(Boolean, default=False)
    country: Mapped[str] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    is_general: Mapped[bool] = mapped_column(Boolean, default=False)

    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))

class Account(Base):
    __tablename__ = 'accounts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True)
    api_id: Mapped[str] = mapped_column(String)
    api_hash: Mapped[str] = mapped_column(String)
    flood_wait: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    active_type: Mapped[str] = mapped_column(String, nullable=True)
