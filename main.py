import asyncio
import os
import discord
from discord.ext import commands
from bot import MarketBot


async def load(bot: commands.Bot):
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


client = MarketBot(command_prefix="!", intents=discord.Intents.all())


async def main():
    async with client:
        await load(client)
        await client.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())
