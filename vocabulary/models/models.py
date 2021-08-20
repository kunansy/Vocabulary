import datetime
import uuid

from sqlalchemy import Column, Unicode, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
now = datetime.datetime.utcnow


def _uuid_gen() -> str:
    return str(uuid.uuid4())


def PrimaryKey(*args, **kwargs) -> Column:
    if len(args) == 0:
        args = UUID,

    kwargs['primary_key'] = True
    kwargs['default'] = kwargs.get('default', _uuid_gen)

    return Column(*args, **kwargs)


class Word(Base):
    __tablename__ = 'words'

    word_id = PrimaryKey(UUID)
    word = Column(Unicode)
    added_at = Column(DateTime, default=now)
    eng_t = ARRAY(Unicode)
    rus_t = ARRAY(Unicode)


class WordToLearn(Base):
    __tablename__ = 'words_to_learn'

    word_id = PrimaryKey(UUID)
    word = Column(Unicode)
    added_at = Column(DateTime, default=now)

