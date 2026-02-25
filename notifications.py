import requests
import os

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            print("📱 Telegram уведомления включены")
    
    def send_notification(self, message):
        """Отправка уведомления в Telegram"""
        if not self.enabled:
            print(f"📱 [УВЕДОМЛЕНИЕ] {message}")
            return True
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Ошибка отправки в Telegram: {e}")
            return False
    
    def notify_new_ticket(self, ticket):
        """Уведомление о новом обращении"""
        message = (
            f"📧 <b>Новое обращение #{ticket.id}</b>\n"
            f"От: {ticket.full_name}\n"
            f"Email: {ticket.email}\n"
            f"Тональность: {ticket.sentiment}\n"
            f"Суть: {ticket.issue_summary}"
        )
        self.send_notification(message)