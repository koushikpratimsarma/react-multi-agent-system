import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
POSTGRES_URI = os.getenv("POSTGRES_URI")
TODAY = datetime.now().strftime("%Y-%m-%d")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is missing from the .env file")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from the .env file")

if not EXA_API_KEY:
    raise ValueError("EXA_API_KEY is missing from the .env file")

if not POSTGRES_URI:
    raise ValueError("POSTGRES_URI is missing from the .env file")



model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)