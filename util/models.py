import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

class Base(DeclarativeBase):
    pass

class Account(Base):
    __tablename__ = 'account'
    id:Mapped[int] = mapped_column(primary_key=True)
    account_number:Mapped[int] = mapped_column(sa.BIGINT)
    name:Mapped[str] = mapped_column(sa.String(32))
    created_on:Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    balance:Mapped[float] = mapped_column(sa.NUMERIC(19,2, asdecimal=False), sa.CheckConstraint('balance >= 0'), server_default=sa.text('0'))
    polls:Mapped[List['PollSubscriber']] = relationship('PollSubscriber', backref='account', cascade='all, delete-orphan')

    __table_args__ = (sa.UniqueConstraint('account_number', 'name', name='account_ukey'),)

class PollSubscriber(Base):
    __tablename__ = 'poll_subscriber'
    id:Mapped[int] = mapped_column(primary_key=True)
    account_id:Mapped[int] = mapped_column(sa.ForeignKey('account.id'))
    poll_id:Mapped[int] = mapped_column(sa.ForeignKey('poll.id'))
    stake:Mapped[float] = mapped_column(sa.NUMERIC(19,2, asdecimal=False), sa.CheckConstraint('stake >= 0'), server_default=sa.text('0'))

    __table_args__ = (sa.UniqueConstraint('account_id', 'poll_id', name='poll_subscriber_ukey'),)

class Poll(Base):
    __tablename__ = 'poll'
    id:Mapped[int] = mapped_column(primary_key=True)
    title:Mapped[str] = mapped_column(sa.String(250))
    created_on:Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    ended_on:Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), sa.CheckConstraint('ended_on > created_on'))
    open:Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.text('True'))
    pool:Mapped[float] = mapped_column(sa.NUMERIC(19,2, asdecimal=False), sa.CheckConstraint('pool >= 0'), server_default=sa.text('0'))
    subscribers:Mapped[List['PollSubscriber']] = relationship('PollSubscriber', backref='poll', cascade='all, delete-orphan')

def create_object[T](cls: type[T], **kwargs) -> T:
    return cls(**kwargs)
