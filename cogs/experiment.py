import os

import discord
from discord import app_commands
from discord.ext import commands

from bot import MarketBot
from util.transformers import Duration
from util.embeds import poll_embed_maker



class ExperimentCog(commands.Cog):
    def __init__(self, client: MarketBot):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{__name__} is online!')

    @app_commands.command(name='parse')
    async def parse_duration(self, interaction: discord.Interaction, duration: Duration):
        await interaction.response.send_message(duration.value)
    
    @app_commands.command(name='total_stake')
    async def get_stake(self, interaction: discord.Interaction, poll_id: int):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get(session, poll_id)
            if poll:
                result = await self.client.db.bets.get_stake_totals(session, poll=poll, granularity=1)
                embed = poll_embed_maker.new_poll(poll, poll.options)
                embed = poll_embed_maker.locked_poll(embed, poll, result)
            
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name='reward')
    async def reward(self, interaction: discord.Interaction, poll_id: int):
        async with self.client.db.async_session() as session:
            poll = await self.client.db.polls.get(session, poll_id)
            if poll:
                winner_stakes = await self.client.db.bets.get_stake_totals(session, poll=poll, winners=True)
                all_stakes = await self.client.db.bets.get_stake_totals(session, poll=poll)
                payout_ratio = sum(all_stakes) / sum(winner_stakes)
                betters = await self.client.db.bets.get_winning_bets(session, poll=poll)

                for better in betters:
                    await self.client.db.accounts.update(session, better.account, balance=better.account.balance+(better.stake*payout_ratio))

                print([(b.account_id, b.stake) for b in betters])
            
        await interaction.response.send_message([stake*payout_ratio for stake in winner_stakes])

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.response.send_message(error, delete_after=30, ephemeral=True)

async def setup(client: MarketBot):
    await client.add_cog(ExperimentCog(client), guild=discord.Object(id=os.getenv('DEBUG_GUILD')))