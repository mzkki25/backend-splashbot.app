from typing import TypedDict, Optional, List, Annotated
from langgraph.graph.message import add_messages

from pydantic import BaseModel, Field

class AgentState(TypedDict):
    session_id: str
    user_id: str
    prompt: str
    chat_option: str
    file_id: Optional[str]
    file_url: Optional[str]
    references: Optional[List[str]]
    response: Optional[str]
    follow_up_question: Optional[str]
    created_at: str
    messages: Annotated[list, add_messages]
    
class DataAnalysisInput(BaseModel):
    chat_option: str = Field(description="The chat option: 2 Wheels, 4 Wheels, Retail General, Retail Beauty, Retail FnB, Retail Drugstore")
    code: str = Field(description="Python code to execute with pandas and plotly. Must set variable 'final_answer' with the result.")