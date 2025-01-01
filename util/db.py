from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from util.models import Base


class Database:
    def __init__(
        self,
        db_name: str,
        user: str,
        passwd: str,
        host: str = "localhost",
        port: int = 5432,
    ):
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{user}:{passwd}@{host}:{port}/{db_name}", echo=True
        )

        self.async_session = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

    async def create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
