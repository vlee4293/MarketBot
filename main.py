from bot import MarketBot
import discord
import os
from discord.ext import commands
import asyncio

async def load(bot: commands.Bot):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')


client = MarketBot(command_prefix='!', intents=discord.Intents.all())

async def main():
    async with client:
        await load(client)
        await client.start(os.getenv('DISCORD_TOKEN'))


asyncio.run(main())

