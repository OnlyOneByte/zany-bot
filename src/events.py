import discord
from datetime import datetime
from discord import User, Reaction, Message
from discord.ext import commands
from .db import add_deleted, check_user_bank, get_deleted_message, DM_SCHEMA, increment_unlock_times

class EventHandler(commands.Cog):
    def __init__(self, client, db_con, config):
        self.client = client
        self.db_con = db_con
        self.config = config

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot Started!")

    @commands.Cog.listener()
    async def on_message_delete(self, message: Message):
        if not message.author.bot and "mudae" not in message.channel.name:
            if self.config['debug'] > 1:
                deleted_text = str(datetime.now())+","+message.channel.name+","+message.author.name+",\""+message.content+"\"\n"
                print("|||DELETED|||", deleted_text, end="")

            attachment_filenames = []
            for attachment in message.attachments:
                filename = 'attachments/'+str(attachment.id)+"."+attachment.filename.split(".")[-1]
                await attachment.save(filename)
                attachment_filenames.append(filename)

            zany_chan = await self.client.fetch_channel(self.config['zany_channel'])
            react_message = await zany_chan.send(f"======\nA Message was deleted in:\n  -{message.guild.name }\n  -{message.channel.name}\n  -**{message.author.name}**\n  -*Cost: {1}*\nReact to this message to get a DM with the deleted message!")

            task = (
                str(datetime.now()),
                react_message.id,
                message.guild.id,
                message.guild.name,
                message.channel.id,
                message.channel.name,
                message.author.id,
                message.author.name,
                message.content,
                ",".join(attachment_filenames),
                0,
            )
            
            add_deleted(self.db_con, task)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User):
        # only zany channel, and only for bot
        if reaction.message.author.id != self.client.user.id and reaction.message.channel.id != self.config['zany_channel']:
            return

        # do blacklist if we want it.
        if self.config['blacklist_user']:
            # blacklist user check. This is so that blacklist is editable.
            blacklisted_user_ids = []
            with open('blacklist.txt', 'r') as f:
                blacklisted_user_ids = f.read().splitlines()
            if str(user.id) in blacklisted_user_ids:
                await user.send("Nice try, but you're blacklisted 🗿")
                return


        # grabs message and checks to see if it is the correct one
        deleted_msg = get_deleted_message(self.db_con, int(reaction.message.id))
        if not deleted_msg:
            return

        # Do economy if we want it
        if self.config['economy_enable']:
            cost = 2**(deleted_msg[DM_SCHEMA['unlock_times']] +1)
            if not check_user_bank(self.db_con, user, cost, self.config['economy']):
                await user.send(f"You do not have enough {self.config['economy']['currency_name']}s! Please wait!")
                return
            else:
                increment_unlock_times(self.db_con, deleted_msg[DM_SCHEMA['react_message_id']],deleted_msg[DM_SCHEMA['user_id']])
                await reaction.message.edit(content=f"======\nA Message was deleted in:\n  -{deleted_msg[DM_SCHEMA['guild_name']]}\n  -{deleted_msg[DM_SCHEMA['channel_name']]}\n  -**{deleted_msg[DM_SCHEMA['user_name']]}**\n  -*Cost: {cost}*\nReact to this message to get a DM with the deleted message!")

        # The magic that happens, showing the user the deleted message
        await user.send("|==== Message by: " + deleted_msg[DM_SCHEMA['user_name']] + " ====|")
        if deleted_msg[DM_SCHEMA['attachments']]:
            msg_files = []
            for filename in deleted_msg[deleted_msg[DM_SCHEMA['attachments']]].split(","):
                file = discord.File(filename)
                msg_files.append(file)
            await user.send(content=deleted_msg[DM_SCHEMA['text']], files=msg_files)
        else:
            await user.send(content=deleted_msg[DM_SCHEMA['text']])
