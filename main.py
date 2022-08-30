
import yaml
import os
import re
import asyncio
import discord
from yaml import SafeLoader
from discord.ext import commands
from src.events import EventHandler
from src.commands import CommandHandler
from src.db import create_connection
from dotenv import load_dotenv
load_dotenv()

async def coin_interval(client, conn, economyOptions, zany_channel):
    await client.wait_until_ready()
    print("Starting up background task: Economy Earn Interval Tiemr")
    zany_chan = await client.fetch_channel(zany_channel)

    # main background loop
    while True:
        await asyncio.sleep(economyOptions['earn_interval']*60)
        await zany_chan.send(f"Everyone is getting paid! You have new {economyOptions['currency_name']}s!")
        conn.execute("UPDATE users SET banked_zanycoins=banked_zanycoins+?", (economyOptions['per_interval_gain'],))
        conn.execute("UPDATE users SET banked_zanycoins=? WHERE banked_zanycoins>?", (economyOptions['max_bank'], economyOptions['max_bank']))
        

async def rob_interval(client, conn, economyOptions, zany_channel):
    await client.wait_until_ready()
    print("Starting up background task: Rob Interval Timer")
    zany_chan = await client.fetch_channel(zany_channel)

    # main background loop
    while True:
        await asyncio.sleep(economyOptions['rob_interval']*60)
        await zany_chan.send("LET THE HUNT BEGIN! ROBS RESET!")
        conn.execute("UPDATE users SET robs_used=0")
        

path_matcher = re.compile(r'\$\{([^}^{]+)\}')
def path_constructor(loader, node):
  ''' Extract the matched value, expand env variable, and replace the match '''
  value = node.value
  match = path_matcher.match(value)
  env_var = match.group()[2:-1]
  return os.environ.get(env_var) + value[match.end():]

def main():
    db_connection = None
    config_options = None
    yaml.add_implicit_resolver('!path', path_matcher, None, SafeLoader)
    yaml.add_constructor('!path', path_constructor, SafeLoader)

    with open("config.yaml", "r") as yamlfile:
        data = yaml.safe_load(yamlfile)
        config_options = data
        db_connection = create_connection(data['sqlite_dir'])

    client = commands.Bot(command_prefix=config_options['command_prefix'], intents=discord.Intents.default()) # register command prefix

    # register background tasks
    if config_options['economy_enable']:
        client.loop.create_task(coin_interval(client, db_connection, config_options['economy'], config_options['zany_channel']))
    if config_options['economy']['rob_enabled']:
        client.loop.create_task(rob_interval(client, db_connection, config_options['economy'], config_options['zany_channel']))
    
    
    client.add_cog(EventHandler(client, db_connection, config_options)) # Registers event handlers
    client.add_cog(CommandHandler(client, db_connection, config_options)) # Registers command handlers
    client.run(config_options['token'])

if __name__ == "__main__":
   try:
      main()
   except KeyboardInterrupt:
      print ("exiting...")
      exit(0)
