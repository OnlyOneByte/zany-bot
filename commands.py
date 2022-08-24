import discord
import random
from discord.ext import commands
from db import add_user

class CommandHandler(commands.Cog):
    def __init__(self, client, db_con, config):
        self.client = client
        self.db_con = db_con
        self.config = config

    @commands.command(aliases=['b', 'bal'])
    async def balance(self, ctx: commands.Context, user: discord.User=None):
        if not ctx.channel.id == int(self.config['zany_channel']):
            msg = await ctx.channel.send("WRONG CHANNEL HOMIE")
            return
        
        user_id = user.id if user else ctx.author.id
        user_name = user.name if user else ctx.author.name
        balance = self.db_con.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not balance:
            add_user(self.db_con, (user_id,user_name,int(self.config['economy']['starting_amount']), 0))
            balance = [self.config['economy']['starting_amount']]
        await ctx.channel.send(f"<@{user_id}> has {balance[0]} zany coins remaining!")

    @commands.command(aliases=['r'])
    async def rob(self, ctx: commands.Context, user: discord.User=None):
        # channel check
        if not ctx.channel.id == int(self.config['zany_channel']):
            msg = await ctx.channel.send("WRONG CHANNEL HOMIE")
            return
        # Args check
        if not user:
            await ctx.channel.send("You need to mention someone to rob!")
            return
        # self reference check
        if user.id == ctx.author.id:
            await ctx.channel.send("You can't rob yourself, silly!")
            return
        # victim balance check
        balance_victim = self.db_con.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (user.id,)).fetchone()
        if balance_victim == None:
            add_user(self.db_con, (user.id,user.name,int(self.config['economy']['starting_amount']), 0))
            balance_victim = [int(self.config['economy']['starting_amount'])]
        if not balance_victim[0] > 0:
            await ctx.channel.send("You are trying to rob someone with 0 coins you sicko.")
            return
        # robber rob usage check
        balance_robber = self.db_con.execute("SELECT banked_zanycoins,robs_used FROM users WHERE user_id=?", (ctx.author.id,)).fetchone()
        if balance_robber== None:
            add_user(self.db_con, (ctx.author.id,ctx.author.name,int(self.config['economy']['starting_amount']), 0))
            balance_robber = [int(self.config['economy']['starting_amount']), 0]
        if not balance_robber[1] < int(self.config['economy']['robs_per_interval']):
            await ctx.channel.send("You have no more robs left. Please wait for your robs to reset.")
            return
        
        # WE ROBBED THEM BITCHEAS
        rob_amount = random.randint(0, balance_victim[0])
        new_bal = balance_robber[0]+rob_amount if balance_robber[0]+rob_amount < self.config['economy']['max_bank'] else self.config['economy']['max_bank']

        self.db_con.execute("UPDATE users SET banked_zanycoins=?, robs_used=robs_used+1 WHERE user_id=?", (new_bal, ctx.author.id))
        self.db_con.execute("UPDATE users SET banked_zanycoins=banked_zanycoins-? WHERE user_id=?" , (rob_amount, user.id))

        await ctx.channel.send(f"<@{ctx.author.id}> has robbed <@{user.id}> for {rob_amount}. You now have {new_bal} zany coins! 😈")
    