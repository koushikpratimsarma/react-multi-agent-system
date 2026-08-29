"""FastAPI application assembly."""

from fastapi import FastAPI

from api.router.chat import router as chat_router
from api.router.root import router as root_router


app = FastAPI(
    title="Multi-Agent System",
    version="1.0.0",
)

app.include_router(root_router)
app.include_router(chat_router)