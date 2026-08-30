"""FastAPI application assembly."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router.chat import router as chat_router
from api.router.root import router as root_router


app = FastAPI(
    title="Multi-Agent System",
    version="1.0.0",
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