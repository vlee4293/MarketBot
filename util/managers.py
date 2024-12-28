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
        balance: Optional[float] = None
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
    ) -> Optional[Account]:
        
        stmt = (
            select(Account).where(
                Account.account_number == account_number
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
        balance: Optional[float] = None
    ) -> Account:
        
        account = await self.get(session, account_number=account_number)
        if account:
            if account.name != name:
                self.update(session, account, name=name)
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
    ) -> None:
        
        stmt = (
            delete(Account).where(
                Account.account_number == account_number,
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
        account: Account,
        question: str, 
        reference: str,
        created_on: datetime, 
        lockin_by: datetime,
        finalized_on: Optional[datetime] = None
    ) -> Poll:
        
        poll = Poll(
            account=account,
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
    
    async def update(
        self,
        session: AsyncSession,
        poll: Poll,
        *,
        account: Optional[Account] = None,
        status: Optional[PollStatus] = None,
        question: Optional[str] = None,
        lockin_by: Optional[datetime] = None,
        finalized_on: Optional[datetime] = None,
        reference: Optional[str] = None
    ) -> None:
        
        if account is not None:
            poll.account = account
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

    async def get_stake_totals(
        self,
        session: AsyncSession,
        *,
        poll: Poll,
        winners: Optional[bool] = None
    ) -> List[float]:
        
        stmt = select(func.sum(Bet.stake)).join(Bet.option, isouter=True, full=True)
        if winners is None:
            stmt = stmt.where(PollOption.poll == poll)
        else:
            stmt = stmt.where(
                PollOption.poll == poll,
                PollOption.winning == winners
            )
        
        stmt = stmt.group_by(PollOption.id)

        query = await session.execute(stmt)
        stakes = query.scalars().all()
        stakes = [stake if stake is not None else 0 for stake in stakes]
        return stakes

    async def get_winning_bets(
        self,
        session: AsyncSession,
        *,
        poll: Poll
    ) -> List[Bet]:
        
        stmt = (
            select(Bet).join(Bet.option)
            .where(
                PollOption.poll_id == poll.id,
                PollOption.winning == True
            )
        )

        query = await session.execute(stmt)
        return query.unique().scalars().all()

    async def update(
        self,
        session: AsyncSession,
        bet: Bet,
        *,
        account: Optional[Account] = None,
        option: Optional[PollOption] = None,
        stake: Optional[float] = None
    ):
        
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
        poll: Optional[Poll] = None,
        index: Optional[int] = None,
        value: Optional[str] = None,
        winning: Optional[bool] = None,
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
           
