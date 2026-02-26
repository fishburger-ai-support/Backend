from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)

    date = Column(DateTime, default=datetime.utcnow)
    full_name = Column(String(200))
    object_name = Column(String(200))
    phone = Column(String(50))
    email = Column(String(120))
    serial_numbers = Column(Text)
    device_type = Column(String(200))
    sentiment = Column(String(50), default="нейтрально")
    issue_summary = Column(Text)

    status = Column(String(50), default="new")
    original_message = Column(Text)
    ai_draft = Column(Text)
    final_answer = Column(Text)
    context = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)