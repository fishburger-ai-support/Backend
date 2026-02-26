from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.ticket import Ticket


class TicketRepository:

    async def create(self, ticket: Ticket):
        async with AsyncSessionLocal() as session:
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            return ticket

    async def get_all(self):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Ticket))
            return result.scalars().all()