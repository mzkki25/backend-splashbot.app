from typing import Optional, List, Literal, Dict, Union
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    email_or_username: str
    password: str

class ChatRequest(BaseModel):
    prompt: str 
    file_id: Optional[str] = None
    chat_options: Literal[
        "General Macroeconomics",
        "2 Wheels",
        "4 Wheels",
        "Retail General",
        "Retail Beauty",
        "Retail FnB",
        "Retail Drugstore"
    ] = Field(default="General Macroeconomics")

class ChatInit(BaseModel):
    chat_options: Literal[
        "General Macroeconomics",
        "2 Wheels",
        "4 Wheels",
        "Retail General",
        "Retail Beauty",
        "Retail FnB",
        "Retail Drugstore"
    ] = Field(default="General Macroeconomics")

class ChatResponse(BaseModel):
    response: str
    file_url: Optional[str] = None

class ChatHistory(BaseModel):
    chat_session_id: str
    title: str
    timestamp: str

class ChatMessage(BaseModel):
    message_id: str
    chat_session_id: str
    role: str  
    content: Union[str, Dict]
    file_id: Optional[str] = None
    timestamp: Optional[str] = None
    references: Optional[List[str]] = None  