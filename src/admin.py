import discord
import random
import time
from discord.ext import commands
from .db import add_user, check_user_bank

class AdminCommandHandler(commands.Cog):
    def __init__(self, client, db_con, config):
        self.client = client
        self.db_con = db_con
        self.config = config

    @commands.command(aliases=['as'])
    async def admin_set(self, ctx: commands.Context, user: discord.User=None, amount: int=None):
        if not ctx.author.id in [132209994165649408]:
            await ctx.channel.send("You are not a discord kitten.")
            return
        # channel check
        if not ctx.channel.id == int(self.config['zany_channel']):
            await ctx.channel.send("WRONG CHANNEL HOMIE")
            return
        # Args check
        if not user:
            await ctx.channel.send("You need to mention someone to give!")
            return
        if not amount:
            await ctx.channel.send("You need to specify an amount!")
            return
        if amount < 0:
            await ctx.channel.send("Nice try, you can't give negative numbers")
            return

        # victim balance check
        balance_receiver = self.db_con.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (user.id,)).fetchone()
        if balance_receiver == None:
            add_user(self.db_con, (user.id,user.name,int(self.config['economy']['starting_amount']), 0))
            balance_receiver = [int(self.config['economy']['starting_amount'])]
        if balance_receiver[0] + amount > int(self.config['economy']['max_bank']):
            await ctx.channel.send("The reciever would not be able to receive that many!")
            return
        self.db_con.execute("UPDATE users SET banked_zanycoins=? WHERE user_id=?" , (amount, user.id))

        f"<@{user.id}>'s balance has been set at {amount}"


