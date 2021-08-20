import datetime
from uuid import UUID

from pydantic import BaseModel, constr


class WordToLearn(BaseModel):
    word: constr(strip_whitespace=True)


class WordToLearnResponse(WordToLearn):
    word_id: UUID
    word: constr(strip_whitespace=True)
    added_at: datetime.datetime


class WordsToLearnListing(WordToLearnResponse):
    words: list[WordToLearnResponse]
