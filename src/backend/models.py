from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    role: str
    content: str
    
class QueryRequest(BaseModel):
    chat_id: str
    content: str
    model: str
    api_key: str
    searchLength: int
    extensionSize: int
    retrieved_docs: List[str]
    messages: List[ChatMessage]  

class QueryResponse(BaseModel):
    chat_id: str
    response: str
