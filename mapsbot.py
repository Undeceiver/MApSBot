#!/usr/bin/env python3.9

import discord
import os
import json
import ast
import datetime
#from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv("test.env")

intents = discord.Intents.default()
intents.message_content = True

server_ids = list(json.loads(os.getenv("SERVER_IDS")))

class MapsBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    
    async def setup_hook(self):
        # This copies the global commands over to the guilds.
        for server_id in server_ids:
            server = discord.Object(id=server_id)

            self.tree.copy_global_to(guild=server)
            await self.tree.sync(guild=server)

        # archivetestplays_task.start()

        return
    
bot = MapsBot(intents=intents)

# This command is probably ugly / not handling things properly. I use it mostly to test.
# Empty default permissions means only administrators can run it. You can also just kill the bot :P
@bot.tree.command()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def shutdown(interaction):
    await interaction.response.send_message('Shutting down... Bye!',ephemeral=True)
    print('Received shutdown command. Shutting down.')
    exit()
    
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


# The mention_instead parameter is used in the case of a failed DM message to send the response on the interaction channel with a mention. If it's False and the DM fails, the message is simply not sent.
async def send_response(interaction, dm=False, mention_instead=False, content = None, **kwargs):
    if dm:
        await send_dm(interaction.user, interaction.channel, mention_instead, content, **kwargs)
    else:
        await interaction.followup.send(content=content, ephemeral=True, **kwargs)

# This should only be used when sending a DM to a user OUTSIDE OF A COMMAND INTERACTION. Use send_response when the message is in response to a command.
# The mention_instead parameter is used in the case of a failed DM message to send the response on the interaction channel with a mention. If it's False and the DM fails, the message is simply not sent.
async def send_dm(user, mention_channel, mention_instead=False, content = None, **kwargs):
    try:
        await user.send(content=content,**kwargs)
    except discord.Forbidden:
        if mention_instead:
            if isinstance(content,str):
                full_content = f'{user.mention} (DM could not be sent)\n\n{content}'
                await mention_channel.send(content=full_content, **kwargs)
            else:
                print(f'Message to user {user.name} could not be sent through direct message.')
        else:
            print(f'Message to user {user.name} could not be sent through direct message.')
            
token = os.getenv("DISCORD_TOKEN")

bot.run(token)