from datetime import datetime

from models.ticket import Ticket
from repositories.ticket_repository import TicketRepository
from services.ai_service import GigaChatClient
from services.email_service import EmailService
from services.notification_service import NotificationService


class TicketService:

    def __init__(self):
        self.repo = TicketRepository()
        self.ai = GigaChatClient()
        self.email = EmailService()
        self.notify = NotificationService()

    async def process_email(self, from_email: str, subject: str, body: str):

        print(f"📧 Получено письмо от {from_email}")

        analysis = await self.ai.analyze_email(body, subject, from_email)

        if not analysis:
            raise Exception("AI не смог обработать письмо")

        decision = analysis.get("decision", "escalate_to_human")

        ticket = Ticket(
            date=datetime.utcnow(),
            full_name=analysis.get("full_name"),
            object_name=analysis.get("object_name"),
            phone=analysis.get("phone"),
            email=from_email,
            serial_numbers=analysis.get("serial_numbers"),
            device_type=analysis.get("device_type"),
            sentiment=analysis.get("sentiment", "нейтрально"),
            issue_summary=analysis.get("issue_summary"),
            original_message=body,
            ai_draft=analysis.get("draft_reply"),
            status="new",
            context={"subject": subject}
        )

        ticket = await self.repo.create(ticket)

        if decision == "full_answer":

            await self.email.send_email(
                to=from_email,
                subject=f"Re: {subject}",
                body=analysis["draft_reply"]
            )

            ticket.status = "answered"
            ticket.final_answer = analysis["draft_reply"]

        elif decision == "need_more_info":

            await self.email.send_email(
                to=from_email,
                subject="Уточнение по обращению",
                body=analysis["draft_reply"]
            )

            ticket.status = "need_info"

        elif decision == "escalate_to_human":

            await self.notify.notify(
                f"⚠️ Новое обращение #{ticket.id}\n"
                f"От: {ticket.full_name}\n"
                f"{ticket.issue_summary}"
            )

            ticket.status = "human_needed"

        await self.repo.update(ticket)

        return ticket