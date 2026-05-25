from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from models import State, College, Contact, Campaign, CampaignSend  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _seed_states()


async def _seed_states():
    from models import State
    from sqlalchemy import select

    states_data = [
        {"name": "Telangana", "code": "TS"},
        {"name": "Andhra Pradesh", "code": "AP"},
        {"name": "Bihar", "code": "BR"},
        {"name": "Jharkhand", "code": "JH"},
        {"name": "Delhi", "code": "DL"},
    ]
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(State))
        existing = result.scalars().all()
        if existing:
            return
        for s in states_data:
            session.add(State(**s))
        await session.commit()
