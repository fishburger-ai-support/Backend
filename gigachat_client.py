import requests
import json
import os
from datetime import datetime, timedelta
import urllib3
from knowledge_base import KnowledgeBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GigaChatClient:
    def __init__(self):
        self.auth_key = os.getenv('GIGACHAT_AUTH_KEY')
        self.client_id = os.getenv('GIGACHAT_CLIENT_ID')
        self.access_token = None
        self.token_expires = None
        self.kb = KnowledgeBase()
        
        if not self.auth_key or not self.client_id:
            raise ValueError("Нет ключей GigaChat в .env")
    
    def _get_access_token(self):
        """Получение токена доступа"""
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': self.client_id,
            'Authorization': f'Basic {self.auth_key}'
        }
        
        data = {'scope': 'GIGACHAT_API_PERS'}
        
        try:
            response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result['access_token']
                
                if 'expires_at' in result:
                    expires_at = datetime.fromisoformat(result['expires_at'].replace('Z', '+00:00'))
                    self.token_expires = expires_at
                else:
                    self.token_expires = datetime.now() + timedelta(minutes=30)
                
                return True
            else:
                print(f"Ошибка получения токена: {response.status_code}")
                return False
        except Exception as e:
            print(f"Ошибка подключения к GigaChat: {e}")
            return False
    
    def _ensure_token(self):
        """Проверка валидности токена"""
        if not self.access_token or datetime.now() >= self.token_expires:
            return self._get_access_token()
        return True
    
    def analyze_email(self, email_text, subject='', sender=''):
        """Анализ письма с использованием GigaChat и базы знаний"""
        
        if not self._ensure_token():
            return self._mock_analysis(email_text)
        
        # Поиск в базе знаний
        similar_docs = self.kb.search(email_text)
        kb_context = ""
        if similar_docs:
            kb_context = "Похожие случаи из базы знаний:\n"
            for doc in similar_docs:
                kb_context += f"--- {doc['title']} ---\n{doc['content']}\n\n"
        
        prompt = f"""{kb_context}

Ты - AI агент техподдержки. Проанализируй письмо и верни ТОЛЬКО JSON в формате:
{{
    "full_name": "ФИО отправителя",
    "object_name": "название организации",
    "phone": "контактный телефон",
    "email": "email отправителя",
    "serial_numbers": "серийные номера приборов через запятую",
    "device_type": "модель или тип устройства",
    "sentiment": "тональность (позитив/нейтрально/негатив/срочно)",
    "issue_summary": "краткое описание проблемы",
    "decision": "full_answer/need_more_info/escalate_to_human",
    "draft_reply": "проект ответа клиенту"
}}

Правила decision:
- full_answer: вся информация есть, вопрос понятен
- need_more_info: не хватает данных (нет серийного номера или модели)
- escalate_to_human: вопрос сложный или клиент очень зол (негатив/срочно)

Письмо:
Тема: {subject}
От: {sender}
Текст: {email_text}

ВЕРНИ ТОЛЬКО JSON, БЕЗ пояснений."""
        
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        data = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, verify=False, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                
                # Извлекаем JSON из ответа
                json_start = answer.find('{')
                json_end = answer.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = answer[json_start:json_end]
                    return json.loads(json_str)
                else:
                    print("Ответ не содержит JSON")
                    return self._mock_analysis(email_text)
            else:
                print(f"Ошибка API: {response.status_code}")
                return self._mock_analysis(email_text)
                
        except Exception as e:
            print(f"Ошибка при анализе: {e}")
            return self._mock_analysis(email_text)
    
    def _mock_analysis(self, email_text):
        """Заглушка на случай недоступности API"""
        print("⚠️ Используется режим заглушки")
        
        # Простой парсим телефон и email регулярками
        import re
        phone_pattern = r'\+7[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        
        phone = re.search(phone_pattern, email_text)
        email = re.search(email_pattern, email_text)
        
        return {
            "full_name": "Не удалось распознать",
            "object_name": "Не удалось распознать",
            "phone": phone.group(0) if phone else "Не указан",
            "email": email.group(0) if email else "Не указан",
            "serial_numbers": "Не указаны",
            "device_type": "Не указан",
            "sentiment": "нейтрально",
            "issue_summary": email_text[:100] + "...",
            "decision": "escalate_to_human",
            "draft_reply": "Здравствуйте! Наш AI-агент временно недоступен. Оператор свяжется с вами в ближайшее время."
        }