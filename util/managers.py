from typing import Optional
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from util.db import Database
from util.models import *
import discord



class AccountManager:
    def __init__(self, db: Database):
        self.__db = db

    async def create_account(self, user: discord.Member) -> Optional[Account]:
        try:
            async with self.__db.async_session() as session:
                async with session.begin():
                    account = create_object(Account, account_number=user.id, name=user.name)
                    session.add(
                        account
                    )
            return account
        except IntegrityError:
            return
    
    async def get_account(self, user: discord.Member) -> Optional[Account]:
        async with self.__db.async_session() as session:
            stmt = select(Account).where(Account.account_number == user.id)
            query = await session.execute(stmt)
            output = query.scalars().one_or_none()
            return output

    async def delete_account(self, user: discord.Member) -> None:
        async with self.__db.async_session() as session:
            async with session.begin():
                stmt = delete(Account).where(Account.account_number == user.id)
                await session.execute(stmt)
    
    async def set_balance(self, user: discord.Member, amount: float, increment: bool) -> None:
        async with self.__db.async_session() as session:
            async with session.begin():
                stmt = select(Account).where(Account.account_number == user.id)
                query = await session.execute(stmt)
                output = query.scalars().one_or_none()

                if output and not increment:
                    output.balance = amount
                elif output:
                    output.balance += amount

class StockManager:
    def __init__(self, db: Database):
        self.__db = db

    async def create_stock(self, ticker: str, name: str) -> Optional[Stock]:
        try:
            async with self.__db.async_session() as session:
                async with session.begin():
                    stock = create_object(Stock, ticker=ticker.upper(), name=name)
                    session.add(stock)
            return stock
        except IntegrityError:
            return
    
    async def get_stock(self, ticker: str) -> Optional[Stock]:
        async with self.__db.async_session() as session:
            stmt = select(Stock).where(Stock.ticker == ticker.upper())
            query = await session.execute(stmt)
            output = query.scalars().one_or_none()
            return output

    async def delete_stock(self, ticker: str) -> None:
        async with self.__db.async_session() as session:
            async with session.begin():
                stmt = delete(Stock).where(Stock.ticker == ticker.upper())
                await session.execute(stmt)

class InvestmentManager:
    def __init__(self, db: Database, account_manager: AccountManager, stock_manager: StockManager):
        self.__db = db
        self.__am = account_manager
        self.__sm = stock_manager

    async def create_investment(self, user: discord.Member, ticker: str, amount: float) -> Optional[Investment]:
        try:
            async with self.__db.async_session() as session:
                account: Account = await self.__am.get_account(user)
                stock: Stock = await self.__sm.get_stock(ticker)

                if account and stock:
                    async with session.begin():
                        investment = create_object(Investment, account_id=account.id, stock_id=stock.id, amount=amount)
                        session.add(investment)
            return investment
        except IntegrityError:
            return
    
    async def get_investments(self, user: discord.Member, ticker: str) -> Optional[List[Investment]]:
        async with self.__db.async_session() as session:
            account: Account = await self.__am.get_account(user)
            stock: Stock = await self.__sm.get_stock(ticker)

            if account and stock:
                stmt = (
                    select(Stock.ticker, Stock.name, func.sum(Investment.amount))
                    .group_by(Stock.ticker, Stock.name)
                    .where(Investment.account_id == account.id and Investment.stock_id == stock.id)
                    .join(Investment.stock)
                )
                query = await session.execute(stmt)
                output = query.all()

            return output

    async def delete_investment(self, user: discord.Member, ticker: str) -> None:
        async with self.__db.async_session() as session:
            account: Account = await self.__am.get_account(user)
            stock: Stock = await self.__sm.get_stock(ticker)

            async with session.begin():
                stmt = select(Investment).where(Investment.account_id == account.id and Investment.stock_id == stock.id)
                await session.execute(stmt)