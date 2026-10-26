from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DocumentOut(BaseModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentDetail(DocumentOut):
    extracted_text: str

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    citations: list[dict]

class SummaryResponse(BaseModel):
    summary: str
