"""Root route that serves the chat UI."""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/")
async def root(request: Request):
    # The page itself is public; protected state lives behind the JWT,
    # which the frontend stores in localStorage and sends as a Bearer
    # token. The chat.js script redirects to /login when no token exists.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )