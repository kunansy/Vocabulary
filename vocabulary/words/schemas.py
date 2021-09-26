import datetime
from uuid import UUID

from pydantic import BaseModel, constr


class WordToLearn(BaseModel):
    word: constr(strip_whitespace=True) # type: ignore


class WordToLearnResponse(WordToLearn):
    word_id: UUID
    added_at: datetime.datetime


class WordsToLearnListing(BaseModel):
    words: list[WordToLearnResponse]


class LinkedWords(BaseModel):
    word: str
    synonyms: list[str]
