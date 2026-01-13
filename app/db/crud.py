from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Ticket, TicketMessage


async def create_ticket(
    session: AsyncSession,
    user_id: int,
    status: str = "open",
) -> Ticket:
    ticket = Ticket(user_id=user_id, status=status)
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def get_ticket(
    session: AsyncSession,
    ticket_id: int,
) -> Optional[Ticket]:
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def get_user_tickets(
    session: AsyncSession,
    user_id: int,
) -> List[Ticket]:
    result = await session.execute(
        select(Ticket).where(Ticket.user_id == user_id).order_by(Ticket.id.desc())
    )
    return list(result.scalars().all())


async def update_ticket_status(
    session: AsyncSession,
    ticket_id: int,
    status: str,
) -> Optional[Ticket]:
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        return None
    ticket.status = status
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def add_ticket_message(
    session: AsyncSession,
    ticket_id: int,
    role: str,
    content: str,
) -> TicketMessage:
    message = TicketMessage(
        ticket_id=ticket_id,
        role=role,
        content=content,
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_ticket_messages(
    session: AsyncSession,
    ticket_id: int,
    limit: Optional[int] = None,
) -> List[TicketMessage]:
    query = select(TicketMessage).where(
        TicketMessage.ticket_id == ticket_id
    ).order_by(TicketMessage.id.asc())
    if limit is not None:
        query = query.limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())
