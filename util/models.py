import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

class Base(DeclarativeBase):
    pass

class Account(Base):
    __tablename__ = 'account'
    id:Mapped[int] = mapped_column(primary_key=True)
    account_number:Mapped[int] = mapped_column(sa.BIGINT, unique=True)
    name:Mapped[str] = mapped_column(sa.String(32))
    created_on:Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    balance:Mapped[float] = mapped_column(sa.NUMERIC(19,2, asdecimal=False), sa.CheckConstraint('balance >= 0'), server_default=sa.text('0'))
    investments:Mapped[List['Investment']] = relationship('Investment', backref='account', cascade='all, delete-orphan')

class Investment(Base):
    __tablename__ = 'investment'
    id:Mapped[int] = mapped_column(primary_key=True)
    account_id:Mapped[int] = mapped_column(sa.ForeignKey('account.id'))
    stock_id:Mapped[int] = mapped_column(sa.ForeignKey('stock.id'))
    created_on:Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    amount:Mapped[float] = mapped_column(sa.NUMERIC(19,2, asdecimal=False), sa.CheckConstraint('amount > 0'))

class Stock(Base):
    __tablename__ = 'stock'
    id:Mapped[int] = mapped_column(primary_key=True)
    ticker:Mapped[str] = mapped_column(sa.String(5), unique=True)
    name:Mapped[str] = mapped_column(sa.String(32))
    investors:Mapped[List['Investment']] = relationship('Investment', backref='stock', cascade='all, delete-orphan')

def create_object[T](cls: type[T], **kwargs) -> T:
    return cls(**kwargs)
