from typing import Optional
from uuid import UUID

import aiohttp
import sqlalchemy.sql as sa
from sqlalchemy.engine import RowMapping

from vocabulary.common import database, settings
from vocabulary.common.log import logger
from vocabulary.models import models


async def _get_json(url: str):
    async with aiohttp.ClientSession() as ses:
        async with ses.get(url) as resp:
            try:
                json = await resp.json()
            except Exception as e:
                logger.exception(e)
                return {}
            return json


async def get_linked_words(word: str) -> list[str]:
    word = word.lower().strip()
    url = settings.SYNONYMS_SEARCH_URL.format(word=word)

    resp = await _get_json(url)

    try:
        words = list(list(resp.values())[0].values())[0].keys()

        words = [
            i.replace('_X', ' sth/sb').replace('_', ' ')
            for i in words
        ]
    except Exception:
        return []
    else:
        return words


async def get_words_to_learn(*,
                             limit: Optional[int] = None,
                             offset: Optional[int] = None) -> list[RowMapping]:
    stmt = sa.select(models.WordToLearn)\
        .order_by(models.WordToLearn.c.added_at)\
        .limit(limit).offset(offset)

    async with database.session() as ses:
        return (await ses.execute(stmt)).mappings().all()


async def delete_word_to_learn(*,
                               word_id: UUID) -> Optional[RowMapping]:
    stmt = sa.delete(models.WordToLearn)\
        .returning(models.WordToLearn)\
        .where(models.WordToLearn.c.word_id == str(word_id))

    async with database.session() as ses:
        return (await ses.execute(stmt)).mappings().one_or_none()


async def add_word_to_learn(*,
                            word: str) -> None:
    stmt = models.WordToLearn.insert()\
        .values(word=word)

    async with database.session() as ses:
        await ses.execute(stmt)
