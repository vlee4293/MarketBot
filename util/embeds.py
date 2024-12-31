
import discord
from datetime import datetime
from typing import List
from util.models import Poll, PollOption

def percentBar(stake):
    segments = round(stake * 10)
    return '`|`' + ':green_square:' * (segments) + ':red_square:' * (10-segments) + '`|`'

class poll_embed_maker:
    @classmethod
    def new_poll(cls, poll: Poll, options: List[PollOption]) -> discord.Embed:
        embed = discord.Embed(title=f'[OPEN] {poll.question}')
        embed.description = f'Poll created by: {poll.account.name}'
        prefixed_options = [f':number_{option.index}: `{option.value}`' for option in sorted(options, key=lambda option: option.index)]
        embed.add_field(name='Options', value='\n'.join(prefixed_options))
        embed.add_field(name='Stake Share (%)', value='\n'.join(list(map(percentBar, [0 for _ in options]))))
        embed.add_field(name='Amount', value='\n'.join([f'${0:.2f}' for _ in options]))
        embed.add_field(name='Place your stake with:', value=f'`/poll bet {poll.id} [option_number] [stake]`', inline=False)
        footer = [
            f'Total stake: ${0:.2f}',
            'Lock in by: '+ datetime.strftime(poll.lockin_by.astimezone(), '%-m/%-d/%y %-I:%M %p'),
        ]
        embed.set_footer(text='\n'.join(footer))
        return embed
    
    @classmethod
    def update_open_poll(cls, original: discord.Embed, poll: Poll, stakes: List[float]):
        total_stake = sum(stakes)
        normal_stakes = [stake / total_stake for stake in stakes]
        original.set_field_at(1, name='Stake Share (%)', value='\n'.join(list(map(percentBar, normal_stakes))))
        original.set_field_at(2, name='Amount', value='\n'.join([f'`${stake:.2f}`' for stake in stakes]))
        footer = [
            f'Total stake: ${total_stake:.2f}',
            'Lock in by: '+ datetime.strftime(poll.lockin_by.astimezone(), '%-m/%-d/%y %-I:%M %p'),
        ]
        original.set_footer(text='\n'.join(footer))
        return original


    @classmethod
    def lock_open_poll(cls, original: discord.Embed, poll: Poll) -> discord.Embed:
        original.title = '[LOCKED] ' + original.title[7:]
        original.set_field_at(3, name='Close the poll with:', value=f'`/poll close {poll.id} [winning_number]`', inline=False)
        total_stake, _ = original.footer.text.split('\n')
        footer = [
            total_stake,
        ]
        original.set_footer(text='\n'.join(footer))
        return original

    @classmethod
    def closed_poll(cls, poll: Poll, winning_option: PollOption) -> discord.Embed:
        embed = discord.Embed(title=f'The poll [`{poll.question:.45}`]({poll.reference}) has finalized')
        embed.add_field(name='Winning Outcome', value=f':number_{winning_option.index}: `{winning_option.value}`')
        return embed
    
    @classmethod
    def close_locked_poll(cls, original: discord.Embed) -> discord.Embed:
        original.title = '[CLOSED] ' + original.title[9:]
        original.remove_field(2)
        return original
    



    
