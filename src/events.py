from datetime import datetime
import discord
from discord import User, Reaction, Message
from discord.ext import commands
from db import add_deleted, add_user, check_user_unlocks, create_connection, get_deleted_message

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
            reacc_message = await zany_chan.send("======\nA Message was deleted in:\n- " + message.guild.name + "\n- " + message.channel.name + "\n- " + message.author.name + "\nReact to this message to get a DM with the deleted message!")

            task = (
                str(datetime.now()),
                reacc_message.id,
                message.guild.id,
                message.channel.id,
                message.author.name,
                message.author.id,
                message.content,
                ",".join(attachment_filenames)
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
            if not check_user_unlocks(self.db_con, user, self.config['economy']):
                await user.send(f"You are out of {self.config['economy']['currency_name']}s! Please wait!")
                return

        # The magic that happens, showing the user the deleted message
        await user.send("|==== Message by: " + deleted_msg[4] + " ====|")
        if deleted_msg[7]:
            msg_files = []
            for filename in deleted_msg[7].split(","):
                file = discord.File(filename)
                msg_files.append(file)
            await user.send(content=deleted_msg[6], files=msg_files)
        else:
            await user.send(content=deleted_msg[6])
