from fastapi import APIRouter, Body
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from vocabulary.common.log import logger
from vocabulary.examples import routes as example_routes
from vocabulary.words import routes as word_routes


router = APIRouter(
    prefix='/view',
    tags=['view']
)

templates = Jinja2Templates(directory="vocabulary/templates")


@router.get('/', response_class=HTMLResponse)
async def get_view(request: Request):
    return templates.TemplateResponse('view.html', {'request': request})


@router.post('/', response_class=HTMLResponse)
async def get_view(request: Request, word: str = Body(...)):
    word = word.split('=')[-1]
    corpus_examples, linked_words = {}, {}

    try:
        corpus_examples = await example_routes.get_corpus_examples(word, pages_count=5)
    except Exception:
        logger.exception("Error getting corpus examples")
    try:
        linked_words = await word_routes.get_link_words(word)
    except Exception:
        logger.exception("Error getting linked words")

    context = {
        'request': request,
        'word': word,
        'corpus_examples': corpus_examples.get('examples', []),
        'linked_words': linked_words.get('synonyms', [])
    }

    return templates.TemplateResponse('view.html', context)
