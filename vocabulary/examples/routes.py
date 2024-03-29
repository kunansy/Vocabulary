from fastapi import APIRouter, Query, params

from vocabulary.examples import schemas, db


router = APIRouter(
    prefix="/examples",
    tags=['examples']
)


@router.get('/corpus/{word}',
            response_model=schemas.CorpusExamples)
async def get_corpus_examples(word: str,
                              pages_count: int = Query(10, ge=1),
                              lang: schemas.LANGUAGES = Query('en')): # type: ignore
    if isinstance(lang, params.Query):
        lang = lang.default # type: ignore
    if isinstance(pages_count, params.Query):
        pages_count = pages_count.default

    examples = await db.get_corpus_examples(
        word=word, mycorp=lang, pages_count=pages_count
    )
    examples.sort(key=lambda ex: len(ex['original']))

    return {
        "examples": examples,
        "count": len(examples),
        "lang": lang
    }


@router.get('/self/{word}',
            response_model=schemas.SelfExamples)
async def get_self_examples(word: str):
    pass
