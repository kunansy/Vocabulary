import datetime
import uuid

from sqlalchemy import Column, Unicode, DateTime, Table, MetaData
from sqlalchemy.dialects.postgresql import UUID, ARRAY


metadata = MetaData()
utcnow = datetime.datetime.utcnow


def _uuid_gen() -> str:
    return str(uuid.uuid4())


def PrimaryKey(*args, **kwargs) -> Column:
    if len(args) == 0:
        args = 'id', UUID
    elif len(args) == 1:
        args = *args, UUID

    kwargs['primary_key'] = True
    kwargs['default'] = kwargs.get('default', _uuid_gen)

    return Column(*args, **kwargs)


Word = Table(
    'words',
    metadata,

    PrimaryKey('word_id'),
    Column('word', Unicode, unique=True),
    Column('added_at', DateTime, default=utcnow),
    Column('eng_t', ARRAY(Unicode), comment='Английские дефиниции слова'),
    Column('rus_t', ARRAY(Unicode), comment='Русские дефиниции слова')
)

WordToLearn = Table(
    'words_to_learn',
    metadata,

    PrimaryKey('word_id', UUID),
    Column('word', Unicode, unique=True),
    Column('added_at', DateTime, default=utcnow)
)
