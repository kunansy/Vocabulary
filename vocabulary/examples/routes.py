from fastapi import APIRouter, Query

from vocabulary.examples import schemas
from fastapi import APIRouter, Query

from vocabulary.examples import schemas


router = APIRouter(
    prefix="/examples",
    tags=['examples']
)


@router.get('/coprus/{word}',
            response_model=schemas.CorpusExamples)
async def get_corpus_examples(word: str,
                              language: schemas.LANGUAGES = Query('en')):
    pass


@router.get('/self/{word}',
            response_model=schemas.SelfExamples)
async def get_self_examples(word: str):
    pass
