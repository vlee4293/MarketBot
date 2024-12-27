import os
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from bot import MarketBot
from util.embeds import poll_embed_maker
from util.models import PollStatus
from util.transformers import Duration, Options


@app_commands.guild_only()
class PollCog(commands.GroupCog, group_name='poll', group_description='Poll commands'):
    def __init__(self, client: MarketBot):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{__name__} is online!')
    
    @app_commands.command(name='create')
    async def create(self, interaction: discord.Interaction, question: str, lockin_duration: Duration, options: Options):  
        """Create a poll
        
        Parameters
        -----------
        question: str
            Provide a question.
        lockin_duration: Duration
            Provide a duration (ex. 1m). Supported units: [m]inutes, [h]ours, [d]ays.
        options: Options
            Provide a list of options seperated by the | symbol.
        """

        await interaction.response.defer()
        message = await interaction.original_response()
    
        async with self.client.db.async_session() as session:
            start_time = datetime.now()
            poll = await self.client.db.polls.create(
                session, 
                question = question,
                reference = message.jump_url,
                created_on = start_time,
                lockin_by = start_time + lockin_duration.value
            )

            poll_options = await self.client.db.options.create_all(
                session,
                poll = poll,
                options = options.values
            )

        embed = poll_embed_maker.new_poll(poll, poll_options)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='bet')
    async def bet(self, interaction: discord.Interaction, poll_id: int, option_number: int, stake: float):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get(session, poll_id)  
            if poll is None:
                raise Exception('There is no poll to bet on stupid')
            if poll.status is not PollStatus.OPEN:
                raise Exception('There is no open poll to bet on stupid')

            if option_number <= 0 and option_number > len(poll.options):
                raise Exception(f'Are you blind? There are clearly only {len(poll.options)} options loser.')
            
            account = await self.client.db.accounts.get_or_create(session, account_number=interaction.user.id, name=interaction.user.name)
            if account.balance < stake:
                raise Exception('You got no money to bet on you broke ass bitch!')

            await self.client.db.accounts.update(session, account, balance=account.balance-stake)
            bet = await self.client.db.bets.get(session, account, poll.options[option_number-1])
            if bet:
                await self.client.db.bets.update(session, bet, stake=bet.stake+stake)
            else:
                await self.client.db.bets.create(session, account=account, option=poll.options[option_number-1], stake=stake)
            
        await interaction.response.send_message(f'${stake:.2f} placed on `{poll.question}`', ephemeral=True)
                
    @app_commands.command(name='close')
    async def close(self, interaction: discord.Interaction, poll_id: int, winning_number: int):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get(session, poll_id)
            if poll is None:
                raise Exception(f'Try y\'know... picking an existing poll?')
            if poll.status is PollStatus.FINALIZED:
                raise Exception(f'`{poll.question}` is already closed.')
            if winning_number <= 0 or winning_number > len(poll.options):
                raise Exception(f'Are you blind? There are clearly only {len(poll.options)} options loser.')

            await self.client.db.options.update(session, poll.options[winning_number-1], winning=True)
            await self.client.db.polls.update(session, poll, status=PollStatus.FINALIZED, finalized_on=datetime.now())

        embed = poll_embed_maker.close_poll(poll, poll.options[winning_number-1])
        await interaction.response.send_message(embed=embed)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            await interaction.response.send_message(error.original, delete_after=30, ephemeral=True)
        else:
            await interaction.response.send_message('An error occurred.', delete_after=30, ephemeral=True)

async def setup(client: MarketBot):
    await client.add_cog(PollCog(client), guild=discord.Object(id=os.getenv('DEBUG_GUILD')))
    
    