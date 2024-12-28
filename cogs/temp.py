import discord
from discord.ext import commands
from discord.embeds import Embed
from bot import MarketBot
from datetime import datetime, timedelta
from discord import app_commands
from typing import Literal
import os


class Market(commands.Cog):
    def __init__(self, client: MarketBot):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        
        print(f'{__name__} is online!')

    @app_commands.guild_only()
    @app_commands.command(name='balance')
    async def balance(self, interaction: discord.Interaction):
        async with self.client.db.async_session() as session:
            account = await self.client.db.accounts.get_or_create(session, account_number=interaction.user.id, name=interaction.user.name)
            embed = Embed(
                title=f'{interaction.user.display_name}\'s Balance', 
                description=f'${account.balance:.2f}'
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(name='reset')
    async def hardreset(self, interaction: discord.Interaction):
        await self.client.db.drop_tables()
        await self.client.db.create_tables()
        await interaction.response.send_message('Tables reset', ephemeral=True)

async def setup(client: MarketBot):
    await client.add_cog(Market(client), guild=discord.Object(id=os.getenv('DEBUG_GUILD')))
