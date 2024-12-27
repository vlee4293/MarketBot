from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, delete, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from util.models import *



class AccountManager:
    async def create(
        self, 
        session: AsyncSession, 
        *,
        account_number: int,
        name: str,
        balance: float = None
    ) -> Account:
        
        account = Account(
            account_number=account_number, 
            name=name, 
            balance=balance
        )
        
        session.add(account)
        await session.commit()
        return account

    async def get(
        self, 
        session: AsyncSession, 
        *,
        account_number: int, 
        name: str
    ) -> Optional[Account]:
        
        stmt = (
            select(Account).where(
                or_(Account.account_number == account_number, Account.name == name)
            )
        )

        query = await session.execute(stmt)
        return query.unique().scalars().one_or_none()
    
    async def get_or_create(
        self, 
        session: AsyncSession, 
        *,
        account_number: int,
        name: str,
        balance: float = None
    ) -> Account:
        
        account = await self.get(session, account_number=account_number, name=name)
        if account:
            return account
        else:
            return await self.create(
                session, 
                account_number=account_number, 
                name=name,
                balance=balance
            )

    async def delete(
        self, 
        session: AsyncSession, 
        *,
        account_number: int, 
        name: str
    ) -> None:
        
        stmt = (
            delete(Account).where(
                Account.account_number == account_number,
                Account.name == name
            )
        )

        await session.execute(stmt)
        await session.commit()
    
    async def update(
        self,
        session: AsyncSession,
        account: Account,
        *,
        account_number: int = None,
        name: str = None,
        balance: float = None
    ) -> None:
        
        if account_number is not None:
            account.account_number = account_number
        if name is not None:
            account.name = name
        if balance is not None:
            account.balance = balance

        await session.commit()

class PollManager:
    async def create(
        self, 
        session: AsyncSession, 
        *,
        question: str, 
        reference: str,
        created_on: datetime, 
        lockin_by: datetime,
        finalized_on: datetime = None
    ) -> Poll:
        
        poll = Poll(
            question=question,
            created_on=created_on,
            lockin_by=lockin_by,
            finalized_on=finalized_on,
            reference=reference
        )

        session.add(poll)
        await session.commit()
        return poll

    async def get(
        self, 
        session: AsyncSession, 
        id: int
    ) -> Optional[Poll]:
        
        stmt = (
            select(Poll).where(
                Poll.id == id
            )
        )

        query = await session.execute(stmt)
        return query.unique().scalars().one_or_none()
    
    async def get_all(
        self, 
        session: AsyncSession, 
        *,
        status: PollStatus
    ) -> List[Poll]:
        
        stmt = select(Poll).where(
            Poll.status == status
        )
        
        query = await session.execute(stmt)
        return query.unique().scalars().all()

    async def delete(
        self, 
        session: AsyncSession, 
        id: int
    ) -> None:
        
        stmt = (
            delete(Poll).where(
                Poll.id == id
            )
        )
        
        await session.execute(stmt)
        await session.commit()
    
    async def update(
        self,
        session: AsyncSession,
        poll: Poll,
        *,
        status: PollStatus = None,
        question: str = None,
        lockin_by: datetime = None,
        finalized_on: datetime = None,
        reference: str = None
    ) -> None:
        
        if status is not None:
            poll.status = status
        if question is not None:
            poll.question = question
        if lockin_by is not None:
            poll.lockin_by = lockin_by
        if finalized_on is not None:
            poll.finalized_on = finalized_on
        if reference is not None:
            poll.reference = reference
        
        await session.commit()
    
class BetManager:
    async def create(
        self,
        session: AsyncSession,
        *,
        account: Account,
        option: PollOption,
        stake: float
    ) -> Bet:
        
        bet = Bet(
            account = account,
            option = option,
            stake = stake
        )

        session.add(bet)
        await session.commit()
        return bet
    
    async def get(
        self,
        session: AsyncSession,
        account: Account,
        option: PollOption
    ) -> Optional[Bet]:
        
        stmt = (
            select(Bet).where(
                Bet.account == account,
                Bet.option == option
            )
        )

        query = await session.execute(stmt)
        return query.unique().scalars().one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        *,
        account: Account,
        option: PollOption,
    ) -> List[Bet]:
        
        stmt = (
            select(Bet).where(
                Bet.account == account,
                Bet.option == option,
            )
        )

        query = await session.execute(stmt)
        return query.unique().scalars().all()

    async def get_total_stake(
        self,
        session: AsyncSession,
        *,
        poll: Poll,
        winners: bool = None
    ) -> float:
        
        if winners is not None:
            stmt = (
                select(func.sum(Bet.stake)).join(Bet.option)
                .where(
                    PollOption.poll == poll,
                    PollOption.winning == winners
                )
                .group_by(PollOption.poll == poll)
            )
        else:
            stmt = (
                select(func.sum(Bet.stake)).join(Bet.option)
                .where(
                    PollOption.poll == poll,
                )
                .group_by(PollOption.poll == poll)
            )


        query = await session.execute(stmt)
        total = query.scalars().one_or_none()
        if total is None:
            return 0
        else:
            return total

    async def update(
        self,
        session: AsyncSession,
        bet: Bet,
        *,
        account: Account = None,
        option: PollOption = None,
        stake: float = None
    ) -> Bet:
        
        if account is not None:
            bet.account = account
        if option is not None:
            bet.option = option
        if stake is not None:
            bet.stake = stake
        
        await session.commit()

class PollOptionManager:
    async def create(
        self,
        session: AsyncSession,
        *,
        poll: Poll,
        index: int,
        value: str,
    ) -> PollOption:
        
        option = PollOption(
            poll = poll,
            index = index,
            value = value,
        )

        session.add(option)
        await session.commit()
        return option
    
    async def create_all(
        self,
        session: AsyncSession,
        *,
        poll: Poll,
        options: List[str],
    ) -> List[PollOption]:
        
        poll_options = [PollOption(poll=poll, index=index+1, value=option) for index, option in enumerate(options)]

        session.add_all(poll_options)
        await session.commit()
        return poll_options
    
    async def get(
        self,
        session: AsyncSession,
        poll: Poll,
        index: int
    ) -> Optional[PollOption]:
        
        stmt = (
            select(PollOption).where(
                PollOption.poll == poll,
                PollOption.index == index
            )
        )

        query = await session.execute(stmt)
        return query.unique().scalars().one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        poll: Poll,
    ) -> List[PollOption]:
        
        stmt = (
            select(PollOption).where(
                PollOption.poll == poll,
            )
            .order_by(PollOption.index.asc())
        )

        query = await session.execute(stmt)
        return query.unique().scalars().all()

    async def delete(
        self,
        session: AsyncSession,
        poll: Poll,
        index: int
    ) -> None:
    
        stmt = (
            delete(PollOption).where(
                PollOption.poll == poll,
                PollOption.index == index
            )
        )

        await session.execute(stmt)
        await session.commit()

    async def update(
        self,
        session: AsyncSession,
        option: PollOption,
        *,
        poll: Poll = None,
        index: int = None,
        value: str = None,
        winning: bool = None,
    ) -> None:
        
        if poll is not None:
            option.poll = poll
        if index is not None:
            option.index = index
        if value is not None:
            option.value = value
        if winning is not None:
            option.winning = winning
        
        await session.commit()
           
