from typing import Optional

from pydantic import BaseModel


class EmailWebhook(BaseModel):
    from_email: str
    subject: str
    body: str


class TicketResponse(BaseModel):
    id: int
    full_name: Optional[str]
    issue_summary: Optional[str]
    status: str

    class Config:
        from_attributes = True