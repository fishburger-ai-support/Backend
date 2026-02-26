from email.message import EmailMessage

import aiosmtplib

from config.settings import settings


class EmailService:

    async def send_email(self, to: str, subject: str, body: str):
        message = EmailMessage()
        message["From"] = settings.EMAIL_ADDRESS
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_SERVER,
            username=settings.EMAIL_ADDRESS,
            password=settings.EMAIL_PASSWORD,
        )