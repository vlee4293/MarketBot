import os
import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from sqlalchemy.exc import DBAPIError
from bot import MarketBot
from util.embeds import poll_embed_maker
from util.models import PollStatus
from util.transformers import Duration, Options

BASE_PRIZE = 100.0


@app_commands.guild_only()
class PollCog(commands.GroupCog, group_name="poll", group_description="Poll commands"):
    def __init__(self, client: MarketBot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    @app_commands.checks.cooldown(1, 5, key=lambda x: (x.guild_id, x.user.id))
    @app_commands.command(name="create")
    async def create(
        self,
        interaction: discord.Interaction,
        question: str,
        lockin_duration: Duration,
        options: Options,
    ):
        """Create a poll

        Parameters
        -----------
        question: str
            Provide a question.
        lockin_duration: Duration
            Provide a duration (ex. 1m). Supported units: [m]inutes, [h]ours, [d]ays.
        options: Options
            Provide a list of options seperated by the | symbol. (2 options min.)
        """

        await interaction.response.defer()
        message = await interaction.original_response()

        async with self.client.db.async_session() as session:
            start_time = datetime.now()

            account = await self.client.db.accounts.get_or_create(
                session,
                guild_id=interaction.guild_id,
                account_number=interaction.user.id,
                name=interaction.user.name,
            )

            poll = await self.client.db.polls.create(
                session,
                account=account,
                question=question,
                reference=message.jump_url,
                created_on=start_time,
                lockin_by=start_time + lockin_duration.value,
            )

            poll_options = await self.client.db.options.create_all(
                session, poll=poll, options=options.values
            )

        embed = poll_embed_maker.new_poll(BASE_PRIZE, poll, poll_options)
        await interaction.followup.send(embed=embed)

    @app_commands.checks.cooldown(1, 5, key=lambda x: (x.guild_id, x.user.id))
    @app_commands.command(name="bet")
    async def bet(
        self,
        interaction: discord.Interaction,
        poll_id: int,
        option_number: int,
        stake: float,
    ):
        """Bet on a poll

        Parameters
        -----------
        poll_id: int
            Provide the ID of the poll.
        option_number: int
            Provide one of the options in the poll.
        stake: float
            The amount of money to bet.
        """

        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get(
                session, interaction.guild_id, poll_id
            )

            stake = round(stake, 2)

            if poll is None:
                raise Exception("There is no poll to bet on stupid")
            if poll.status is not PollStatus.OPEN:
                raise Exception("There is no open poll to bet on stupid")
            if option_number <= 0 or option_number > len(poll.options):
                raise Exception(
                    f"Are you blind? There are clearly only {len(poll.options)} options loser."
                )
            if stake <= BASE_PRIZE * 0.25:
                raise Exception("We are not paying you.")

            account = await self.client.db.accounts.get_or_create(
                session,
                guild_id=interaction.guild_id,
                account_number=interaction.user.id,
                name=interaction.user.name,
            )

            if account.balance < stake:
                raise Exception("You got no money to bet on you broke ass bitch!")

            await self.client.db.accounts.update(
                session, account, balance=account.balance - stake
            )

            option = sorted(poll.options, key=lambda x: x.index)[option_number - 1]

            bet = await self.client.db.bets.get(session, account, option)

            if bet:
                await self.client.db.bets.update(session, bet, stake=bet.stake + stake)
            else:
                await self.client.db.bets.create(
                    session,
                    account=account,
                    option=option,
                    stake=stake,
                )

            stakes = await self.client.db.bets.get_stake_totals(session, poll=poll)

        await interaction.response.send_message(
            f"${stake:.2f} placed on :number_{option.index}:`{option.value}` for [`{poll.question:.45}`]({poll.reference})",
            ephemeral=True,
        )

        _, channel_id, message_id = list(map(int, poll.reference[29:].split("/")))
        channel = self.client.get_channel(channel_id)
        msg = await channel.fetch_message(message_id)
        embed = poll_embed_maker.update_open_poll(
            BASE_PRIZE, msg.embeds[0], poll, stakes
        )

        await msg.edit(embed=embed)

    @app_commands.command(name="close")
    @app_commands.checks.cooldown(1, 5, key=lambda x: (x.guild_id, x.user.id))
    async def close(
        self, interaction: discord.Interaction, poll_id: int, winning_number: int
    ):
        """Close a poll you created.

        Parameters
        -----------
        poll_id: int
            Provide the ID of the poll.
        winning_number: int
            Provide a winning option.
        """

        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get(
                session, interaction.guild_id, poll_id
            )

            if poll is None:
                raise Exception("Try y'know... picking an existing poll?")
            if poll.status is PollStatus.FINALIZED:
                raise Exception(f"`{poll.question}` is already closed.")
            if winning_number <= 0 or winning_number > len(poll.options):
                raise Exception(
                    f"Are you blind? There are clearly only {len(poll.options)} options loser."
                )

            account = await self.client.db.accounts.get_or_create(
                session,
                guild_id=interaction.guild_id,
                account_number=interaction.user.id,
                name=interaction.user.name,
            )

            if poll.account != account:
                raise Exception("You do not own this poll.")

            _, channel_id, message_id = list(map(int, poll.reference[29:].split("/")))
            channel = self.client.get_channel(channel_id)
            msg = await channel.fetch_message(message_id)
            embed = msg.embeds[0]

            if poll.status is PollStatus.OPEN:
                await self.client.db.polls.update(
                    session, poll, status=PollStatus.LOCKED, lockin_by=datetime.now()
                )

                embed = poll_embed_maker.lock_open_poll(embed, poll)

            await self.client.db.options.update(
                session, poll.options[winning_number - 1], winning=True
            )

            await self.client.db.polls.update(
                session, poll, status=PollStatus.FINALIZED, finalized_on=datetime.now()
            )

            winner_stakes = await self.client.db.bets.get_stake_totals(
                session, poll=poll, winners=True
            )

            if sum(winner_stakes) > 0:
                all_stakes = await self.client.db.bets.get_stake_totals(
                    session, poll=poll
                )

                payout_ratio = (BASE_PRIZE + sum(all_stakes)) / sum(winner_stakes)

                betters = await self.client.db.bets.get_winning_bets(session, poll=poll)

                for better in betters:
                    await self.client.db.accounts.update(
                        session,
                        better.account,
                        balance=better.account.balance + (better.stake * payout_ratio),
                    )

        closed_embed = poll_embed_maker.closed_poll(
            poll, sorted(poll.options, key=lambda x: x.index)[winning_number - 1]
        )
        await interaction.response.send_message(embed=closed_embed)
        embed = poll_embed_maker.close_locked_poll(embed)
        await msg.edit(embed=embed)

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if not isinstance(error.__cause__, DBAPIError):
            if isinstance(error, app_commands.CommandOnCooldown):
                await interaction.response.send_message(
                    "Command on cooldown. Wait atleast 5 seconds.",
                    ephemeral=True,
                    delete_after=300,
                )
                return
            if isinstance(error, app_commands.CommandInvokeError) or isinstance(
                error, app_commands.TransformerError
            ):
                await interaction.response.send_message(
                    error.__cause__, ephemeral=True, delete_after=300
                )
                return

        await interaction.response.send_message(
            "An error occurred.", ephemeral=True, delete_after=300
        )


async def setup(client: MarketBot):
    guild_id = os.getenv("DEBUG_GUILD")
    if guild_id:
        await client.add_cog(PollCog(client), guild=discord.Object(id=guild_id))
    else:
        await client.add_cog(PollCog(client))
