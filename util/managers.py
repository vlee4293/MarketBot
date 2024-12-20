from typing import Optional
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from util.db import Database
from util.models import *
import discord
from datetime import timedelta



class AccountManager:
    async def create_account(self, session: AsyncSession, user: discord.Member) -> None:
        account = create_object(Account, account_number=user.id, name=user.name)
        session.add(account)
        await session.commit()

    async def get_account(self, session: AsyncSession, user: discord.Member) -> Optional[Account]:
        stmt = select(Account).where(Account.account_number == user.id)
        query = await session.execute(stmt)
        return query.scalars().one_or_none()
    
    async def get_or_create_account(self, session: AsyncSession, user: discord.Member) -> Account:
        output = await self.get_account(session, user)

        if output:
            return output
        else:
            await self.create_account(session, user)
            return await self.get_or_create_account(session, user)

    async def delete_account(self, session: AsyncSession, user: discord.Member) -> None:
        stmt = delete(Account).where(Account.account_number == user.id)
        await session.execute(stmt)
        await session.commit()
    
    async def set_balance(self, session: AsyncSession, user: discord.Member, amount: float, increment: bool) -> None:
        account: Account = await self.get_or_create_account(session, user)
        
        if increment:
            account.balance += amount
        else:
            account.balance = amount
        
        await session.commit()

class PollManager:
    async def create_poll(self, session: AsyncSession, title: str, deadline: datetime) -> None:
        poll = create_object(Poll, title=title, ended_on=deadline)
        session.add(poll)
        await session.commit()

    async def get_poll(self, session: AsyncSession, id: int) -> Optional[Poll]:
        stmt = select(Poll).where(Poll.id == id)
        query = await session.execute(stmt)
        return query.scalars().one_or_none

    async def get_polls(self, session: AsyncSession, open: bool = None) -> Optional[List[Poll]]:
        if open is None:
            stmt = select(Poll).order_by(Poll.created_on.desc())
        else:
            stmt = select(Poll).where(Poll.open == open).order_by(Poll.created_on.desc())
        query = await session.execute(stmt)
        return query.scalars().all()

    async def delete_poll(self, session: AsyncSession, id: int) -> None:
        stmt = delete(Poll).where(Poll.id == id)
        await session.execute(stmt)
        await session.commit()
    
    async def set_state(self, session: AsyncSession, id: int, open: bool) -> None:
        poll = await self.get_poll(session, id)
        if poll:
            poll.open = open
            await session.commit()
    
    async def set_deadline(self, session: AsyncSession, id: int, deadline: datetime) -> None:
        poll = await self.get_poll(session, id)
        if poll:
            if poll.open:
                poll.ended_on = deadline
                await session.commit()

class PollSubscriberManager:
    async def subscribe(self, session: AsyncSession, account: Account, poll: Poll, stake: float) -> None:
        try:
            subscriber = create_object(PollSubscriber, account_id=account.id, poll_id=poll.id, stake=stake)
            session.add(subscriber)
            await session.commit()
        except IntegrityError:
            stmt = select(PollSubscriber).where(PollSubscriber.account_id == account.id and PollSubscriber.poll_id == poll.id)
            query = await session.execute(stmt)
            entry = query.scalars().one()

            entry.stake += stake
            await session.commit()

    
    async def unsubscribe(self, session: AsyncSession, account: Account, poll: Poll) -> None:
        stmt = delete(PollSubscriber).where(PollSubscriber.account_id == account.id and PollSubscriber.poll_id == poll.id)
        await session.execute(stmt)
        await session.commit()