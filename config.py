import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
POSTGRES_URI = os.getenv("POSTGRES_URI") or os.getenv("DATABASE_URL")
TODAY = datetime.now().strftime("%Y-%m-%d")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is missing from the .env file")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from the .env file")

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
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


TEST_USERS = [
    {"username": "user1", "password": "test1234"},
    {"username": "user2", "password": "test1234"},
    {"username": "user3", "password": "test1234"},
    {"username": "user4", "password": "test1234"},
    {"username": "user5", "password": "test1234"},
]



model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)