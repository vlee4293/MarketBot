from util import Database
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DB_USER = os.getenv('DB_USER')
DB_PASSWD = os.getenv('DB_PASSWD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
db = Database(user=DB_HOST, passwd=DB_PASSWD, db_name=DB_NAME, host=DB_HOST, port=DB_PORT)

@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(f'{bot.user} is connected to the server: {guild.name}(id: {guild.id})')


@bot.command()
async def open(ctx: commands.Context):
    account = await db.accounts.create_account(ctx.author)
    if account:
        await ctx.send('Welcome ' + ctx.author.display_name)
    else:
        await ctx.send('Account already exists.')

@bot.command()
async def reset(ctx: commands.Context):
    await db.accounts.delete_account(ctx.author)
    await db.accounts.create_account(ctx.author)

@bot.command()
async def close(ctx: commands.Context):
    await db.accounts.delete_account(ctx.author)

@bot.command()
async def balance(ctx: commands.Context):
    account = await db.accounts.get_account(ctx.author)
    await ctx.send(f'Balance: ${account.balance:.2f}')

@bot.command()
async def daily(ctx: commands.Context):
    await db.accounts.set_balance(ctx.author, 100, increment=True)

@bot.command()
async def add_stock(ctx: commands.Context):
    await db.stocks.create_stock('cum', 'Cumming Inc.')

@bot.command()
async def invest(ctx: commands.Context):
    await db.investments.create_investment(ctx.author, 'cum', 200)

@bot.command()
async def portfolio(ctx: commands.Context):
    investments = await db.investments.get_investments(ctx.author, 'cum')
    await ctx.send(investments)


bot.run(TOKEN)