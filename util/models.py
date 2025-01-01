import enum
import sqlalchemy as sa
from datetime import datetime
from typing import List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

__all__ = ["Account", "Bet", "Poll", "PollOption", "PollStatus"]


class Base(DeclarativeBase):
    pass


class PollStatus(enum.Enum):
    OPEN = "open"
    LOCKED = ("locked",)
    FINALIZED = "finalized"


class Account(Base):
    __tablename__ = "account"
    __table_args__ = (
        sa.CheckConstraint("balance >= 0"),
        sa.UniqueConstraint("guild_id", "account_number", "name", name="account_ukey"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(sa.BIGINT)
    account_number: Mapped[int] = mapped_column(sa.BIGINT)
    name: Mapped[str] = mapped_column(sa.String(32))
    created_on: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    balance: Mapped[float] = mapped_column(
        sa.NUMERIC(19, 2, asdecimal=False), server_default=sa.text("1000")
    )

    bets: Mapped[List["Bet"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", lazy="joined"
    )
    polls: Mapped[List["Poll"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", lazy="joined"
    )


class Bet(Base):
    __tablename__ = "bet"
    __table_args__ = (
        sa.UniqueConstraint("account_id", "option_id", name="bet_ukey"),
        sa.CheckConstraint("stake > 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(sa.ForeignKey("account.id"))
    option_id: Mapped[int] = mapped_column(sa.ForeignKey("poll_option.id"))
    created_on: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    stake: Mapped[float] = mapped_column(sa.NUMERIC(19, 2, asdecimal=False))

    account: Mapped["Account"] = relationship(
        back_populates="bets", cascade="all", lazy="joined", innerjoin=True
    )
    option: Mapped["PollOption"] = relationship(
        back_populates="bets", cascade="all", lazy="joined", innerjoin=True
    )


class Poll(Base):
    __tablename__ = "poll"
    __table_args__ = (
        sa.CheckConstraint("lockin_by > created_on"),
        sa.CheckConstraint("finalized_on > created_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(sa.ForeignKey("account.id"))
    status: Mapped[PollStatus] = mapped_column(default=PollStatus.OPEN)
    question: Mapped[str] = mapped_column(sa.String(250))
    created_on: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    lockin_by: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    finalized_on: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("'infinity'::timestamp")
    )
    reference: Mapped[str] = mapped_column(sa.String(100), unique=True)

    options: Mapped[List["PollOption"]] = relationship(
        back_populates="poll",
        cascade="all, delete-orphan",
        lazy="joined",
        innerjoin=True,
    )
    account: Mapped["Account"] = relationship(
        back_populates="polls", cascade="all", lazy="joined", innerjoin=True
    )


class PollOption(Base):
    __tablename__ = "poll_option"
    __table_args__ = (
        sa.UniqueConstraint("poll_id", "index", name="poll_option_ukey"),
        sa.CheckConstraint("index > 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(sa.ForeignKey("poll.id"))
    index: Mapped[int] = mapped_column(sa.Integer)
    value: Mapped[str] = mapped_column(sa.String(250))
    winning: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.text("False"))

    bets: Mapped[List["Bet"]] = relationship(
        back_populates="option", cascade="all, delete-orphan", lazy="joined"
    )
    poll: Mapped["Poll"] = relationship(
        back_populates="options", cascade="all", lazy="joined", innerjoin=True
    )
