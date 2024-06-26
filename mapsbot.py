#!/usr/bin/env python3.9

from http import server
import discord
import os
import json
import ast
import datetime
import asyncio
import sys
#from discord.ext import commands
from discord import app_commands
from discord.enums import ButtonStyle
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv("test.env")

intents = discord.Intents.default()
intents.message_content = True

server_ids = list(json.loads(os.getenv("SERVER_IDS")))
bot_id = int(os.getenv("BOT_ID"))
rule_channel_id = int(os.getenv("RULE_CHANNEL_ID"))
rule_post_id = int(os.getenv("RULE_POST_ID"))
rule_reaction_id = int(os.getenv("RULE_REACTION_ID"))
appreciator_role_id = int(os.getenv("APPRECIATOR_ROLE_ID"))
modmail_channel_id = int(os.getenv("MODMAIL_CHANNEL"))
modmail_inbox_id = int(os.getenv("MODMAIL_INBOX"))
modmail_color = int(os.getenv("MODMAIL_COLOR"),16)
map_spotlight_request_channel_id = int(os.getenv("MAP_SPOTLIGHT_REQUEST_CHANNEL"))
map_spotlight_request_inbox_id = int(os.getenv("MAP_SPOTLIGHT_REQUEST_INBOX"))
playlist_spotlight_request_channel_id = int(os.getenv("PLAYLIST_SPOTLIGHT_REQUEST_CHANNEL"))
playlist_spotlight_request_inbox_id = int(os.getenv("PLAYLIST_SPOTLIGHT_REQUEST_INBOX"))
spotlight_color = int(os.getenv("SPOTLIGHT_COLOR"),16)
role_request_channel_id = int(os.getenv("ROLE_REQUEST_CHANNEL"))
role_request_inbox_id = int(os.getenv("ROLE_REQUEST_INBOX"))
role_request_color = int(os.getenv("ROLE_REQUEST_COLOR"),16)

class MapsBot(discord.Client):   
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.server_obj = None

    
    async def setup_hook(self):
        # This copies the global commands over to the guilds.
        for server_id in server_ids:
            server = discord.Object(id=server_id)

            self.tree.copy_global_to(guild=server)
            await self.tree.sync(guild=server)

        # archivetestplays_task.start()

        # We consider the first server in the list to be The server and thus the one where new things will be generated.
        server_id = server_ids[0]
        self.server_obj = await bot.fetch_guild(server_id)
        await self.server_obj.fetch_roles()

        return
    
bot = MapsBot(intents=intents)

# This command is probably ugly / not handling things properly. I use it mostly to test.
# Empty default permissions means only administrators can run it. You can also just kill the bot :P
@bot.tree.command()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def shutdown(interaction):
    await interaction.response.send_message('Shutting down... Bye!',ephemeral=True)
    botlog('Received shutdown command. Shutting down.')
    exit()
    
@bot.event
async def on_ready():
    botlog(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.id != bot_id:
        for channel_id, callback in channel_callbacks.items():
            if message.channel.id == channel_id:
                await callback(message)
    #else:
        #botlog(f"Ignoring self-message: {message.content}")
           
@bot.event
async def on_raw_reaction_add(payload):
    #botlog(f"DEBUG: raw reaction added")
    if payload.message_id == rule_post_id and payload.emoji.id == rule_reaction_id:
        user = await bot.server_obj.fetch_member(payload.user_id)
        channel = await bot.server_obj.fetch_channel(rule_channel_id)
        message = await channel.fetch_message(rule_post_id)
        if not isinstance(user,discord.Member):
            botlog(f"Non-member tried to obtain Appreciator role: {user.name} (ID: {user.id})")
            await send_dm(user,mention_channel=None,mention_instead=False,
                          content=f"There was an error assigning you the Appreciator role, as you don't appear to be a member of the server. This has been recorded, but feel free to reach out to Undeceiver if you do not understand the problem.")
            return
        else:
            role = bot.server_obj.get_role(appreciator_role_id)
            
            await user.add_roles(role,reason="Reaction role")
            await message.remove_reaction(payload.emoji,user)


async def role_request(message):
    await role_request_process(message.content,message.author,message.created_at)
    await message.delete()

async def role_request_process(message:str, user, timestamp):
    botlog(f"Role request: {message} || From: {user.display_name} (ID: {user.id})")
    
    role_request_inbox_channel = bot.get_channel(role_request_inbox_id)
    
    embed = discord.Embed(
        title = f"Role request",
        color = role_request_color,
        timestamp = timestamp,
        description = message,        
    )
    
    embed.set_author(name=f"{user.name} ({user.id})")
    embed.add_field(name="User", value=user.mention, inline=True)
    
    await send_in_channel(role_request_inbox_channel,embeds=[embed])
    await send_dm(user,mention_channel = None, mention_instead = False, content = f"Roles requested.", embeds=[embed])

async def map_spotlight_request(message):
    await map_spotlight_request_process(message.content,message.author,message.created_at)
    await message.delete()

async def map_spotlight_request_process(message:str, user, timestamp):
    botlog(f"Map spotlight request: {message} || From: {user.display_name} (ID: {user.id})")
    
    map_spotlight_request_inbox_channel = bot.get_channel(map_spotlight_request_inbox_id)
    
    embed = discord.Embed(
        title = f"Map spotlight request",
        color = spotlight_color,
        timestamp = timestamp,
        description = message,        
    )
    
    embed.set_author(name=f"{user.name} ({user.id})")
    embed.add_field(name="User", value=user.mention, inline=True)
    
    await send_in_channel(map_spotlight_request_inbox_channel,embeds=[embed])
    await send_dm(user,mention_channel = None, mention_instead = False, content = f"The following map spotlight request has been submitted.", embeds=[embed])

async def playlist_spotlight_request(message):
    await playlist_spotlight_request_process(message.content,message.author,message.created_at)
    await message.delete()

async def playlist_spotlight_request_process(message:str, user, timestamp):
    botlog(f"Playlist spotlight request: {message} || From: {user.display_name} (ID: {user.id})")
    
    playlist_spotlight_request_inbox_channel = bot.get_channel(playlist_spotlight_request_inbox_id)
    
    embed = discord.Embed(
        title = f"Playlist spotlight request",
        color = spotlight_color,
        timestamp = timestamp,
        description = message,        
    )
    
    embed.set_author(name=f"{user.name} ({user.id})")
    embed.add_field(name="User", value=user.mention, inline=True)

    await send_in_channel(playlist_spotlight_request_inbox_channel,embeds=[embed])
    await send_dm(user,mention_channel = None, mention_instead = False, content = f"The following playlist spotlight request has been submitted.", embeds=[embed])

async def modmail_channel(message):
    await modmail_process(message.content, message.author, message.channel, message.created_at)
    await message.delete()

@bot.tree.command(description="Request moderator action privately. Use only for serious matters.")
async def modmail(interaction, message:str):
    await interaction.response.defer(ephemeral=True)
    await modmail_process(message, interaction.user, interaction.channel, interaction.created_at)
    await send_response(interaction,dm=False,mention_instead=False,content=f"Moderators have received your request: '{message}'. Thank you.")

async def modmail_process(message:str, user, channel, timestamp):
    botlog(f"Modmail: {message} || From: {user.display_name} (ID: {user.id}) || In: #{channel.name}")
    
    modmail_inbox_channel = bot.get_channel(modmail_inbox_id)
    
    embed = discord.Embed(
        title = f"Modmail",
        color = modmail_color,
        timestamp = timestamp,
        description = message,
        #url=interaction.channel.jump_url        
    )
    
    embed.set_author(name=f"{user.name} ({user.id})")
    embed.add_field(name="User", value=user.mention, inline=True)
    embed.add_field(name="Channel", value=channel.mention, inline=True)

    await send_in_channel(modmail_inbox_channel,embeds=[embed])

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
                botlog(f'Message to user {user.name} could not be sent through direct message.')
        else:
            botlog(f'Message to user {user.name} could not be sent through direct message.')
    
async def send_in_channel(channel, content = None, embeds = None, **kwargs):
    await channel.send(content=content,embeds = embeds, **kwargs)

def botlog(str):
    time = datetime.datetime.now()
    
    print(f"[{time}] {str}")
    sys.stdout.flush()
    
    
channel_callbacks = {
    modmail_channel_id: modmail_channel,
    map_spotlight_request_channel_id: map_spotlight_request,
    playlist_spotlight_request_channel_id: playlist_spotlight_request,
    role_request_channel_id: role_request,
}

token = os.getenv("DISCORD_TOKEN")

bot.run(token)