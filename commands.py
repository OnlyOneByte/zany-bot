from discord.ext import commands
from db import add_deleted, add_user, check_user_unlocks, create_connection, get_deleted_message

class CommandHandler(commands.Cog):
    def __init__(self, client, db_con, config):
        self.client = client
        self.db_con = db_con
        self.config = config

    @commands.command()
    async def balance(self, ctx: commands.Context):
        if not ctx.channel.id == int(self.config['zany_channel']):
            msg = await ctx.channel.send("WRONG CHANNEL HOMIE")
            return

        balance = self.db_con.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (ctx.author.id,)).fetchone()
        if balance:
            await ctx.channel.send("You have " + str(balance[0]) + " zany coins remaining!")
        else:
            add_user(self.db_con, (ctx.author.id,ctx.author.name,self.config['economy']['starting_amount']))
            await ctx.channel.send("You have " + str(self.config['economy']['starting_amount']) + " zany coins remaining!")
