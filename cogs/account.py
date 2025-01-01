import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.embeds import Embed
from bot import MarketBot


class AccountCog(commands.Cog):
    def __init__(self, client: MarketBot):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} is online!")

    @app_commands.guild_only()
    @app_commands.command(name="balance")
    async def balance(self, interaction: discord.Interaction):
        """View your balance."""
        async with self.client.db.async_session() as session:
            account = await self.client.db.accounts.get_or_create(
                session,
                guild_id=interaction.guild_id,
                account_number=interaction.user.id,
                name=interaction.user.name,
            )

            embed = Embed(
                title=f"{interaction.user.display_name}'s Balance",
                description=f"${account.balance:.2f}",
            )

            raw_bets = await self.client.db.bets.get_all_active_by_account(
                session, account
            )
            if len(raw_bets) > 0:
                parsed_bets = {
                    "Pending Poll": tuple(
                        f"[`{bet.option.poll.question:.20}`]({bet.option.poll.reference})"
                        for bet in raw_bets
                    ),
                    "Option": tuple(
                        f":number_{bet.option.index}: `{bet.option.value:.10}`"
                        for bet in raw_bets
                    ),
                    "Stake": tuple(f"`${bet.stake:.2f}`" for bet in raw_bets),
                }

                for name, values in parsed_bets.items():
                    embed.add_field(name=name, value="\n".join(values))

            await interaction.response.send_message(embed=embed)


async def setup(client: MarketBot):
    guild_id = os.getenv("DEBUG_GUILD")
    if guild_id:
        await client.add_cog(AccountCog(client), guild=discord.Object(id=guild_id))
    else:
        await client.add_cog(AccountCog(client))
