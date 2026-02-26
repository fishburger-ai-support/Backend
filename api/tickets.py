from fastapi import APIRouter, HTTPException

from schemas.ticket import EmailWebhook
from services.ticket_service import TicketService

router = APIRouter()
service = TicketService()


@router.post("/webhook/email")
async def handle_email(data: EmailWebhook):

    try:
        ticket = await service.process_email(
            from_email=data.from_email,
            subject=data.subject,
            body=data.body
        )

        return {
            "status": "ok",
            "ticket_id": ticket.id,
            "ticket_status": ticket.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tickets")
async def get_tickets():
    tickets = await service.repo.get_all()
    return tickets