import re
from datetime import timedelta
from typing import NamedTuple, List
import discord



class Duration(NamedTuple):
    value: timedelta

    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str):
        m = re.match(r'^\d+[mhd]', value)
        if m:
            match m.string[-1]:
                case 'm':
                    duration = timedelta(minutes=int(m.string[:-1]))
                case 'h':
                    duration = timedelta(hours=int(m.string[:-1]))
                case 'd':
                    duration = timedelta(days=int(m.string[:-1]))
            return cls(value=duration)
        else:
            raise Exception('Invalid duration.')
    
class Options(NamedTuple):
    values: List[str]

    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str):
        raw_options = value.split(sep='|')
        stripped_options = list(map(str.strip, raw_options))
        return cls(values=stripped_options)