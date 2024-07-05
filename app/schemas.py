from pydantic import BaseModel
from typing import Optional, List, Union

class HistoryItem(BaseModel):
    role: str
    parts: str

class Chatbot(BaseModel):
    question:str = ""
    history: Union[List[HistoryItem], None] = list()



