"""FastAPI application assembly."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db.database import init_db
from api.router.chat import router as chat_router
from api.router.root import router as root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the chat_messages / tool_calls tables if they do not exist yet.
    # This makes the app work against a fresh PostgreSQL database (e.g. on
    # Render) without manual schema setup.
    #
    # init_db() is intentionally synchronous because the CLI entry point
    # (main.py) also uses it. Running it in a worker thread here keeps the
    # event loop free during startup.
    await asyncio.to_thread(init_db)
    yield


app = FastAPI(
    title="Multi-Agent System",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root_router)
app.include_router(chat_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}