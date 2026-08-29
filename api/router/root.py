"""Health and root routes."""

from fastapi import APIRouter


router = APIRouter()


@router.get("/")
def root() -> dict[str, str]:
    return {"message": "Agent API is running"}