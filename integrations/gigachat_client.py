from datetime import datetime, timedelta

import httpx

from config.settings import settings


class GigaChatClient:

    def __init__(self):
        self.auth_key = settings.GIGACHAT_AUTH_KEY
        self.client_id = settings.GIGACHAT_CLIENT_ID
        self.access_token = None
        self.token_expires = None

    async def _get_token(self):

        async with httpx.AsyncClient(timeout=30, verify=False) as client:

            response = await client.post(
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                headers={
                    "Authorization": f"Basic {self.auth_key}",
                    "RqUID": self.client_id,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"scope": "GIGACHAT_API_PERS"}
            )

            data = response.json()
            self.access_token = data["access_token"]
            self.token_expires = datetime.utcnow() + timedelta(minutes=25)

    async def _ensure_token(self):
        if not self.access_token or datetime.utcnow() >= self.token_expires:
            await self._get_token()

    async def chat(self, prompt: str):

        await self._ensure_token()

        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            response = await client.post(
                "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                },
                json={
                    "model": "GigaChat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
            )

            return response.json()