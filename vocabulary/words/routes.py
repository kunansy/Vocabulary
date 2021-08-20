from uuid import UUID

from fastapi import APIRouter, Query, HTTPException

from vocabulary.words import schemas, db


router = APIRouter(
    prefix="/words",
    tags=['words']
)


@router.get('/to-learn/list',
            response_model=schemas.WordsToLearnListing)
async def get_words_to_learn(p: int = Query(1, ge=1),
                             page_size: int = Query(10, ge=1)):
    """ List words to learn """
    offset = (p - 1) * page_size

    words = await db.get_words_to_learn(
        limit=page_size, offset=offset
    )

    return {
        'words': words
    }


@router.post('/to-learn/add')
async def add_word_to_learn(word: schemas.WordToLearn):
    """ Add word to learn """
    await db.add_word_to_learn(word=word.word)


@router.delete('/to-learn/{word_id}',
               response_model=schemas.WordToLearnResponse)
async def remove_word_to_learn(word_id: UUID):
    """ Remove the word """
    if (word := await db.delete_word_to_learn(word_id=word_id)) is None:
        raise HTTPException(status_code=404)

    return word
