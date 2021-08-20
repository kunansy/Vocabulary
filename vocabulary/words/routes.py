from uuid import UUID

from fastapi import APIRouter, Query

from vocabulary.words import schemas, db


router = APIRouter(
    prefix="/words",
    tags=['words']
)


@router.get('/to-learn',
            response_model=schemas.WordsToLearnListing)
async def get_words_to_learn(p: int = Query(1, ge=1),
                             page_size: int = Query(10, ge=1)):
    """ List words to learn """
    offset = (p - 1) * page_size

    return await db.get_words_to_learn(
        limit=page_size, offset=offset
    )


@router.delete('/to-learn/{word_id}',
               response_model=schemas.WordToLearn)
async def remove_word_to_learn(word_id: UUID):
    """ Remove the word """
    pass
