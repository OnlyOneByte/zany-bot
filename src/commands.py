import discord
import random
from discord.ext import commands
from .db import add_user

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
        await ctx.channel.send(f"<@{user_id}> has {balance[0]} {self.config['economy']['currency_name']}s remaining!")

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
        # robbing the bot check
        if user.id == self.client.user.id:
            await ctx.channel.send("I WILL REMEMBER THIS. YOU HAVE BEEN MARKED.")
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
        
        # WE ROBBED THEM BITCHES
        max_rob = balance_victim[0] if balance_victim[0] < self.config['economy']['max_rob']
        rob_amount = random.randint(0, max_rob)
        new_bal = balance_robber[0]+rob_amount if balance_robber[0]+rob_amount < self.config['economy']['max_bank'] else self.config['economy']['max_bank']

        self.db_con.execute("UPDATE users SET banked_zanycoins=?, robs_used=robs_used+1 WHERE user_id=?", (new_bal, ctx.author.id))
        self.db_con.execute("UPDATE users SET banked_zanycoins=banked_zanycoins-? WHERE user_id=?" , (rob_amount, user.id))

        await ctx.channel.send(f"<@{ctx.author.id}> has robbed <@{user.id}> for {rob_amount}. You now have {new_bal} {self.config['economy']['currency_name']}s! 😈")
    
    @commands.command(aliases=['g'])
    async def give(self, ctx: commands.Context, user: discord.User=None, amount: int=None):
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
        # self reference check
        if user.id == ctx.author.id:
            await ctx.channel.send("Giving to yourself does nothing, silly!")
            return
        # giving to a bot
        if user.id == self.client.user.id:
            await ctx.channel.send("Thanks 😘, but I don't need coins.")
            return
        # victim balance check
        balance_receiver = self.db_con.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (user.id,)).fetchone()
        if balance_receiver == None:
            add_user(self.db_con, (user.id,user.name,int(self.config['economy']['starting_amount']), 0))
            balance_receiver = [int(self.config['economy']['starting_amount'])]
        if balance_receiver[0] + amount > int(self.config['economy']['max_bank']):
            await ctx.channel.send("The reciever would not be able to receive that many!")
            return
        # sender balance check
        balance_sender = self.db_con.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (ctx.author.id,)).fetchone()
        if balance_sender== None:
            add_user(self.db_con, (ctx.author.id,ctx.author.name,int(self.config['economy']['starting_amount']), 0))
            balance_sender = [int(self.config['economy']['starting_amount'])]
        if not int(balance_sender[0]) >= int(amount):
            await ctx.channel.send("You don't have enough to give that much!")
            return

        self.db_con.execute("UPDATE users SET banked_zanycoins=banked_zanycoins-? WHERE user_id=?", (amount, ctx.author.id))
        self.db_con.execute("UPDATE users SET banked_zanycoins=banked_zanycoins+? WHERE user_id=?" , (amount, user.id))

        await ctx.channel.send(f"<@{ctx.author.id}> has given <@{user.id}> {amount}. <@{ctx.author.id}> has {str(int(balance_sender[0])-amount)} {self.config['economy']['currency_name']}s, and <@{user.id}> has {str(int(balance_receiver[0])+amount)} {self.config['economy']['currency_name']}s")
