from fastapi import APIRouter


router = APIRouter(
    prefix="/words",
    tags=['words']
)
