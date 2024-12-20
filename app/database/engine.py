import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from dotenv import load_dotenv
from app.database.models import Base

load_dotenv()

engine = create_async_engine(os.getenv('DB_URL'))

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
