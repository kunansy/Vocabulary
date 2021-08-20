import datetime
from uuid import UUID

from pydantic import BaseModel, constr


class WordToLearn(BaseModel):
    word: constr(strip_whitespace=True)


class WordToLearnResponse(WordToLearn):
    word_id: UUID
    word: constr(strip_whitespace=True)
    added_at: datetime.datetime


class WordsToLearnListing(WordToLearn):
    eng_t: list[constr(strip_whitespace=True)]
    rus_t: list[constr(strip_whitespace=True)]

    @validator('eng_t')
    def validate_eng_t(cls,
                       eng_t: str) -> list[str]:
        return eng_t.split(';')

    @validator('rus_t')
    def validate_rus_t(cls,
                       rus_t: str) -> list[str]:
        return rus_t.split(';')
