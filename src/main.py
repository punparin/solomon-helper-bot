import os
from discord import Embed, Colour
from discord_components import DiscordComponents, ComponentsBot, Button, SelectOption, Select
import discord.ext.commands as commands
from Logger import Logger
from SolomonShop import SolomonShop


logger = Logger()
solomonShop = SolomonShop(logger)

client = commands.Bot("!")
DiscordComponents(client)

@client.event
async def on_ready():
    print("{0} is now online!".format(client.user))

@client.event
async def on_message(ctx):
    await solomonShop.process(client, ctx)


if __name__ == "__main__":
    discord_token = os.getenv('DISCORD_TOKEN')
    client.run(discord_token)
