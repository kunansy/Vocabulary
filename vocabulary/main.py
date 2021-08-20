import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from vocabulary.common import settings, database
from vocabulary.common.log import logger
from vocabulary.words.routes import router as words_router
from vocabulary.examples.routes import router as examples_router


app = FastAPI(
    title="Vocabulary API",
    version=settings.API_VERSION,
    debug=settings.API_DEBUG
)

app.include_router(words_router)
app.include_router(examples_router)


async def database_exception_handler(request: Request,
                                     exc: database.DatabaseError):
    logger.exception("Error with the database, %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request,
                                       exc: RequestValidationError):
    logger.exception("Validation error occurred, %s", str(exc))
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error"},
    )


if __name__ == '__main__':
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=settings.API_DEBUG
    )
