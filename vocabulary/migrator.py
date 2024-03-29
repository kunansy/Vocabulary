#!/usr/bin/env python3
""" It helps to migrate the data from sqlite
to the current postgresql database
"""
import argparse
import asyncio
import sqlite3
from contextlib import contextmanager
from typing import Iterator

import requests

from vocabulary.common import database
from vocabulary.common.log import logger
from vocabulary.models import models


API_HOST = 'http://127.0.0.1:9001'


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect('../eng.db')
    try:
        yield conn
        conn.commit()
    except Exception as e:
        logger.exception(e)
        raise
    finally:
        conn.close()


def get_words_to_learn() -> list[str]:
    stmt = """
    SELECT word FROM words_to_learn;
    """

    with session() as ses:
        return [
            word[0]
            for word in ses.execute(stmt).fetchall()
        ]


def insert_words_to_learn(words: list[str]) -> None:
    for word in words:
        logger.debug("Inserting word to learn '%s'", word)
        resp = requests.post(f"{API_HOST}/words/to-learn/add", json={"word": word})
        resp.raise_for_status()


def migrate_words_to_learn() -> None:
    words = get_words_to_learn()
    logger.info(f"Migrating {len(words)} words to learn...")
    insert_words_to_learn(words)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate data from old sqlite db to current PostgreSQL"
    )
    parser.add_argument(
        '--migrate',
        action="store_true",
        help="Make migrations",
        dest="migrate"
    )
    parser.add_argument(
        '--create-schema',
        action="store_true",
        help="Create all tables",
        dest="create_schema"
    )
    args = parser.parse_args()

    if args.create_schema:
        async with database.engine.begin() as conn:
            await conn.run_sync(models.metadata.create_all)

    if args.migrate:
        migrate_words_to_learn()


if __name__ == '__main__':
    asyncio.run(main())
