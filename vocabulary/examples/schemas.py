from typing import Literal

from pydantic import BaseModel
from rnc import mycorp


LANGUAGES = Literal[tuple(
    k for k in mycorp.Parallel.__dict__.keys()
    if k[0].islower()
)]


class CorpusExamples(BaseModel):
    pass


class SelfExamples(BaseModel):
    pass