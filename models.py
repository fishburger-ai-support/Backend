from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 9 полей для таблицы
    date = db.Column(db.DateTime, default=datetime.utcnow)
    full_name = db.Column(db.String(200))
    object_name = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    serial_numbers = db.Column(db.Text)
    device_type = db.Column(db.String(200))
    sentiment = db.Column(db.String(50), default='нейтрально')
    issue_summary = db.Column(db.Text)
    
    # Служебные поля
    status = db.Column(db.String(50), default='new')
    original_message = db.Column(db.Text)
    ai_draft = db.Column(db.Text)
    final_answer = db.Column(db.Text)
    context = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Все поля для API"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'full_name': self.full_name,
            'object_name': self.object_name,
            'phone': self.phone,
            'email': self.email,
            'serial_numbers': self.serial_numbers,
            'device_type': self.device_type,
            'sentiment': self.sentiment,
            'issue_summary': self.issue_summary,
            'status': self.status,
            'original_message': self.original_message,
            'ai_draft': self.ai_draft,
            'final_answer': self.final_answer,
            'context': self.context
        }
    
    def for_table(self):
        """Только 9 полей для отображения в таблице"""
        return {
            'date': self.date.isoformat() if self.date else None,
            'full_name': self.full_name or '',
            'object_name': self.object_name or '',
            'phone': self.phone or '',
            'email': self.email or '',
            'serial_numbers': self.serial_numbers or '',
            'device_type': self.device_type or '',
            'sentiment': self.sentiment or 'нейтрально',
            'issue_summary': self.issue_summary or '',
            'id': self.id,
            'status': self.status
        }