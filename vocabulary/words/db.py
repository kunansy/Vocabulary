from typing import Optional

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