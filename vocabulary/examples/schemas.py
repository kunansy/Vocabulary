from typing import Literal

from pydantic import BaseModel, HttpUrl, validator
from rnc import mycorp


LANGUAGES = Literal[tuple(
    k for k in mycorp.Parallel.__dict__.keys()
    if k[0].islower()
)]


class CorpusExample(BaseModel):
    original: str
    native: str
    src: str
    ambiguation: bool
    doc_url: HttpUrl
    found_wordforms: set[str]

    @validator('ambiguation', pre=True)
    def validate_ambiguation(cls,
                             amb: str) -> bool:
        print(amb)
        return amb.lower() == 'disambiguated'


class CorpusExamples(BaseModel):
    examples: list[CorpusExample]
    count: int = 0

    @validator('count', pre=True, always=True)
    def validate_count(cls,
                       count: int,
                       values) -> int:
        print(values)
        return len(values['examples'])


class SelfExamples(BaseModel):
    pass
