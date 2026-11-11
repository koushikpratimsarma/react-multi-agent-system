
import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
POSTGRES_URI = os.getenv("POSTGRES_URI") or os.getenv("DATABASE_URL")

# NVIDIA configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv(
    "NVIDIA_BASE_URL",
    "https://integrate.api.nvidia.com/v1"
)
NVIDIA_MODEL = os.getenv(
    "NVIDIA_MODEL",
    "nvidia/nemotron-3.5-lightning-30b-a3b"
)

TODAY = datetime.now().strftime("%Y-%m-%d")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is missing from the .env file")

if not EXA_API_KEY:
    raise ValueError("EXA_API_KEY is missing from the .env file")

if not POSTGRES_URI:
    raise ValueError("POSTGRES_URI is missing from the .env file")

# JWT authentication
JWT_SECRET = os.getenv("JWT_SECRET") or "CHANGE_ME_IN_PRODUCTION"

if JWT_SECRET == "CHANGE_ME_IN_PRODUCTION":
    print("[WARN] JWT_SECRET is not set - using an insecure default. "
          "Set a random value in .env before deploying.")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") or "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)

# Model provider selection
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "nvidia").lower()

if MODEL_PROVIDER == "nvidia":
    if not NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY is missing from the .env file")

    model = ChatOpenAI(
        model=NVIDIA_MODEL,
        api_key=NVIDIA_API_KEY,
        base_url=NVIDIA_BASE_URL,
        temperature=0,
    )

elif MODEL_PROVIDER == "openai":
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is missing from the .env file")

    model = ChatOpenAI(
        model="gpt-4.1-mini",
        api_key=OPENAI_API_KEY,
        temperature=0,
    )

else:
    raise ValueError(f"Unsupported MODEL_PROVIDER: {MODEL_PROVIDER}")
