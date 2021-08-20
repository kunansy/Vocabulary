import datetime
from uuid import UUID

from pydantic import BaseModel, constr, validator


class WordToLearn(BaseModel):
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
