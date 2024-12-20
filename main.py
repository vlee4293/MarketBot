from bot import MarketBot, TOKEN
import discord





client = MarketBot(command_prefix='!', intents=discord.Intents.all())


    

client.run(TOKEN)
