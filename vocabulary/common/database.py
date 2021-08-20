from contextlib import asynccontextmanager
from typing import AsyncContextManager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from vocabulary.common import settings
from vocabulary.common.log import logger


class DatabaseError(Exception):
    pass


dsn = settings.DB_DSN_TEMPLATE.format(
    username=settings.DB_USERNAME,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT
)
engine = create_async_engine(
    dsn,
    isolation_level=settings.DB_ISOLATION_LEVEL
)


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
