from typing import Optional
from uuid import UUID

from sqlalchemy.engine import RowMapping
import sqlalchemy.sql as sa

from vocabulary.common import database
from vocabulary.models import models


async def get_words_to_learn(*,
                             limit: Optional[int] = None,
                             offset: Optional[int] = None) -> list[RowMapping]:
    stmt = sa.select(models.WordToLearn)\
        .limit(limit).offset(offset)

    async with database.session() as ses:
        return (await ses.execute(stmt)).mappings().all()


async def delete_word_to_learn(*,
                               word_id: UUID) -> Optional[RowMapping]:
    stmt = sa.delete(models.WordToLearn)\
        .returning(models.WordToLearn)\
        .where(models.WordToLearn.word_id == word_id)

    async with database.session() as ses:
        return (await ses.execute(stmt)).mappings().one_or_none()