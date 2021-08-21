from fastapi import APIRouter, Query

from vocabulary.examples import schemas
from fastapi import APIRouter, Query

from vocabulary.examples import schemas, db


router = APIRouter(
    prefix="/examples",
    tags=['examples']
)


@router.get('/coprus/{word}',
            response_model=schemas.CorpusExamples)
async def get_corpus_examples(word: str,
                              pages_count: int = Query(10, ge=1),
                              language: schemas.LANGUAGES = Query('en')):
    return await db.get_corpus_examples(
        word=word, mycorp=language, pages_count=pages_count
    )


@router.get('/self/{word}',
            response_model=schemas.SelfExamples)
async def get_self_examples(word: str):
    pass
