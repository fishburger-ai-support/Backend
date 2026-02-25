import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailHandler:
    def __init__(self):
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.mail.ru')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.mail.ru')
        self.email = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.enabled = all([self.imap_server, self.smtp_server, self.email, self.password])
        
        if self.enabled:
            print("📧 Почтовый клиент инициализирован")
        else:
            print("⚠️ Почтовый клиент отключён (нет данных в .env)")
    
    def fetch_new_emails(self, limit=10):
        """Получение новых непрочитанных писем"""
        if not self.enabled:
            return []
        
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email, self.password)
            mail.select('inbox')
            
            _, messages = mail.search(None, 'UNSEEN')
            
            emails = []
            for msg_id in messages[0].split()[:limit]:
                _, msg_data = mail.fetch(msg_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Получаем текст письма
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                emails.append({
                    'from': msg.get('From', ''),
                    'subject': msg.get('Subject', ''),
                    'body': body,
                    'date': msg.get('Date', '')
                })
            
            mail.close()
            mail.logout()
            return emails
            
        except Exception as e:
            print(f"Ошибка получения почты: {e}")
            return []
    
    def send_email(self, to, subject, body):
        """Отправка письма"""
        if not self.enabled:
            print(f"📧 [РЕЖИМ ЗАГЛУШКИ] Письмо к {to}: {subject}")
            return True
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP_SSL(self.smtp_server)
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Письмо отправлено {to}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False