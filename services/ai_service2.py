import json
import logging
from datetime import datetime, timedelta

import httpx
from config.settings import settings
from knowledge_base.mock_kb import MockKnowledgeBase


logger = logging.getLogger("GigaChatClient")


class GigaChatClient:

    def __init__(self):
        self.auth_key = settings.GIGACHAT_AUTH_KEY
        self.client_id = settings.GIGACHAT_CLIENT_ID
        self.access_token = None
        self.token_expires = None
        self.kb = MockKnowledgeBase()

        logger.info("Инициализация GigaChatClient")

        if not self.auth_key or not self.client_id:
            logger.error("Нет ключей GigaChat в .env")
            raise ValueError("Нет ключей GigaChat в .env")

    async def _get_access_token(self):

        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": self.client_id,
            "Authorization": f"Basic {self.auth_key}",
        }

        data = {"scope": "GIGACHAT_API_PERS"}

        logger.debug(f"OAuth URL: {url}")
        logger.debug(f"OAuth Headers: {headers}")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, headers=headers, data=data)

            logger.debug(f"OAuth status: {response.status_code}")
            logger.debug(f"OAuth body: {response.text}")

            if response.status_code != 200:
                logger.error("OAuth не 200")
                return False

            result = response.json()
            self.access_token = result.get("access_token")

            expires_value = result.get("expires_at")

            if isinstance(expires_value, str):
                self.token_expires = datetime.fromisoformat(
                    expires_value.replace("Z", "+00:00")
                )
            elif isinstance(expires_value, int):
                self.token_expires = datetime.utcfromtimestamp(expires_value)
            else:
                self.token_expires = datetime.utcnow() + timedelta(minutes=30)

            logger.info("Токен успешно получен")
            return True

        except Exception as e:
            logger.exception("Ошибка подключения к OAuth")
            return False

    async def _ensure_token(self):
        if not self.access_token or datetime.utcnow() >= self.token_expires:
            logger.debug("Обновляем токен")
            return await self._get_access_token()
        return True

    async def analyze_email(self, email_text, subject="", sender=""):

        logger.info(f"Анализ письма от {sender}")

        if not await self._ensure_token():
            logger.warning("Токен не получен, fallback")
            return self._mock_analysis(email_text)

        prompt = f"""
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
- full_answer: вся информация есть
- need_more_info: не хватает данных
- escalate_to_human: сложный или негативный кейс

Письмо:
Тема: {subject}
От: {sender}
Текст: {email_text}

ВЕРНИ ТОЛЬКО JSON, БЕЗ пояснений.
"""

        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        data = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": prompt}],
        }

        logger.debug(f"Chat URL: {url}")
        logger.debug(f"Chat headers: {headers}")
        logger.debug(f"Chat payload: {data}")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, headers=headers, json=data)

            logger.debug(f"Chat status: {response.status_code}")
            logger.debug(f"Chat body: {response.text}")

            if response.status_code != 200:
                logger.error("Chat API вернул не 200")
                return self._mock_analysis(email_text)

            result = response.json()
            answer = result["choices"][0]["message"]["content"]

            json_start = answer.find("{")
            json_end = answer.rfind("}") + 1

            return json.loads(answer[json_start:json_end])

        except Exception:
            logger.exception("Ошибка при вызове chat API")
            return self._mock_analysis(email_text)

    def _mock_analysis(self, email_text):
        logger.warning("Используется mock режим")

        return {
            "decision": "escalate_to_human",
            "draft_reply": "AI временно недоступен."
        }