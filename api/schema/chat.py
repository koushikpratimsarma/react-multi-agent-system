from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str = Field(min_length=1)

class ToolCall(BaseModel):
    """Represents a tool that was called"""
    tool_name: str
    description: str = ""
    timestamp: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
   