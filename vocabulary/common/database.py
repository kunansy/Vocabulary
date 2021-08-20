from contextlib import asynccontextmanager
from typing import AsyncContextManager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from vocabulary.common import settings
from vocabulary.common.log import logger
from vocabulary.models.models import Base


class DatabaseError(Exception):
    pass


def get_dsn(driver: str = 'asyncpg') -> str:
    return settings.DB_DSN_TEMPLATE.format(
        driver=driver,
        username=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        name=settings.DB_NAME
    )


engine = create_async_engine(
    get_dsn(),
    isolation_level=settings.DB_ISOLATION_LEVEL
)
sync_engine = create_engine(
    get_dsn('psycopg2'),
    isolation_level=settings.DB_ISOLATION_LEVEL
)
Base.metadata.create_all(sync_engine)


@asynccontextmanager
async def session(**kwargs) -> AsyncContextManager[AsyncSession]:
    new_ses = AsyncSession(bind=engine, expire_on_commit=False, **kwargs)
    try:
        yield new_ses
        await new_ses.commit()
    except Exception as e:
        await new_ses.rollback()
        logger.exception(e)
        raise DatabaseError(e) from e
    finally:
        await new_ses.close()
