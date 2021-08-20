import datetime
from uuid import UUID

from pydantic import BaseModel, constr, validator


class WordToLearn(BaseModel):
    word_id: UUID
    word: constr(strip_whitespase=True)
    added_at: datetime.datetime


class WordsToLearnListing(WordToLearn):
    eng_t: list[constr(strip_whitespase=True)]
    rus_t: list[constr(strip_whitespase=True)]

    @validator('eng_t')
    def validate(cls,
                 eng_t: str) -> list[str]:
        return eng_t.split(';')

    @validator('rus_t')
    def validate(cls,
                 rus_t: str) -> list[str]:
        return rus_t.split(';')
