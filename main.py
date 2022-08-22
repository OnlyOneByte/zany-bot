from click import command
import discord
from discord import User, Reaction, Message
from datetime import datetime
import yaml
import asyncio
from discord.ext import commands

from db import add_deleted, add_user, check_user_unlocks, create_connection, get_deleted_message


# Globals
# load configs
DB_CONNECTION = None
CONFIG_OPTIONS = None
with open("zany_config.yaml", "r") as yamlfile:
    data = yaml.load(yamlfile, Loader=yaml.FullLoader)
    CONFIG_OPTIONS = data
    DB_CONNECTION = create_connection(data['sqlite_dir'])

# register commands
client = commands.Bot(command_prefix=CONFIG_OPTIONS['command_prefix'])

@client.event
async def on_ready():
    print("Bot Started!")

@client.event
async def on_message_delete(message: Message):
    global DB_CONNECTION, CONFIG_OPTIONS

    if not message.author.bot and "mudae" not in message.channel.name:
        if CONFIG_OPTIONS['debug'] > 1:
            deleted_text = str(datetime.now())+","+message.channel.name+","+message.author.name+",\""+message.content+"\"\n"
            print("|||DELETED|||", deleted_text, end="")

        attachment_filenames = []
        for attachment in message.attachments:
            filename = 'attachments/'+str(attachment.id)+"."+attachment.filename.split(".")[-1]
            await attachment.save(filename)
            attachment_filenames.append(filename)

        zany_chan = await client.fetch_channel(CONFIG_OPTIONS['zany_channel'])
        reacc_message = await zany_chan.send("=================================\nA Message was deleted in:\n- " + message.guild.name + "\n- " + message.channel.name + "\n- " + message.author.name + "\nReact to this message to get a DM with the deleted message!")

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
        
        add_deleted(DB_CONNECTION, task)

@client.event
async def on_reaction_add(reaction: Reaction, user: User):
    global CONFIG_OPTIONS

    # only zany channel, and only for bot
    if reaction.message.author.id != client.user.id and reaction.message.channel.id != CONFIG_OPTIONS['zany_channel']:
        return

    # do blacklist if we want it.
    if CONFIG_OPTIONS['blacklist_user']:
        # blacklist user check. This is so that blacklist is editable.
        blacklisted_user_ids = []
        with open('blacklist.txt', 'r') as f:
            blacklisted_user_ids = f.read().splitlines()
        if str(user.id) in blacklisted_user_ids:
            await user.send("Nice try, but you're blacklisted 🗿")
            return


    # grabs message and checks to see if it is the correct one
    deleted_msg = get_deleted_message(DB_CONNECTION, int(reaction.message.id))
    if not deleted_msg:
        return

    # Do economy if we want it
    if CONFIG_OPTIONS['economy_enable']:
        if not check_user_unlocks(DB_CONNECTION, user, CONFIG_OPTIONS['economy']):
            await user.send("You are out of zany_coins! Please wait!")
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


async def coin_interval(conn, economyOptions, zany_channel):
    await client.wait_until_ready()
    print("Starting up background task of items")
    zany_chan = await client.fetch_channel(zany_channel)

    # main background loop
    while True:
        await zany_chan.send("Everyone is getting paid! You have new zany coins!")
        conn.execute("UPDATE users SET banked_zanycoins=banked_zanycoins+?", (economyOptions['per_interval_gain'],))
        conn.execute("UPDATE users SET banked_zanycoins=? WHERE banked_zanycoins>?", (economyOptions['max_bank'], economyOptions['max_bank']))
        await asyncio.sleep(economyOptions['earn_interval']*60) # task runs every 60 seconds


@client.command()
async def balance(ctx: commands.Context):
    global DB_CONNECTION, CONFIG_OPTIONS
    if not ctx.channel.id == int(CONFIG_OPTIONS['zany_channel']):
        msg = await ctx.channel.send("WRONG CHANNEL HOMIE")
        return

    balance = DB_CONNECTION.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (ctx.author.id,)).fetchone()
    if balance:
        await ctx.channel.send("You have " + str(balance[0]) + " zany coins remaining!")
    else:
        add_user(DB_CONNECTION, (ctx.author.id,ctx.author.name,CONFIG_OPTIONS['economy']['starting_amount']))
        await ctx.channel.send("You have " + str(CONFIG_OPTIONS['economy']['starting_amount']) + " zany coins remaining!")

def main():
    global DB_CONNECTION, CONFIG_OPTIONS, client

    # register background tasks
    if CONFIG_OPTIONS['economy_enable']:
        client.loop.create_task(coin_interval(DB_CONNECTION, CONFIG_OPTIONS['economy'], CONFIG_OPTIONS['zany_channel']))
    
    # run client
    client.run(CONFIG_OPTIONS['token'])

if __name__ == "__main__":
   try:
      main()
   except KeyboardInterrupt:
      print ("exiting...")
      exit(0)
