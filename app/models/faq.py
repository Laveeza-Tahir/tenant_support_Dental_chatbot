from pydantic import BaseModel

class FAQ(BaseModel):
    question: str
    answer: str
    source: str
