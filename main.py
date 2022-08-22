
import yaml
import asyncio
from discord.ext import commands
from events import EventHandler
from commands import CommandHandler
from db import create_connection




async def coin_interval(client, conn, economyOptions, zany_channel):
    await client.wait_until_ready()
    print("Starting up background task of items")
    zany_chan = await client.fetch_channel(zany_channel)

    # main background loop
    while True:
        await zany_chan.send("Everyone is getting paid! You have new zany coins!")
        conn.execute("UPDATE users SET banked_zanycoins=banked_zanycoins+?", (economyOptions['per_interval_gain'],))
        conn.execute("UPDATE users SET banked_zanycoins=? WHERE banked_zanycoins>?", (economyOptions['max_bank'], economyOptions['max_bank']))
        await asyncio.sleep(economyOptions['earn_interval']*60) # task runs every 60 seconds




def main():
    db_connection = None
    config_options = None

    with open("zany_config.yaml", "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        config_options = data
        db_connection = create_connection(data['sqlite_dir'])

    client = commands.Bot(command_prefix=config_options['command_prefix']) # register command prefix

    # register background tasks
    if config_options['economy_enable']:
        client.loop.create_task(coin_interval(client, db_connection, config_options['economy'], config_options['zany_channel']))
    
    client.add_cog(EventHandler(client, db_connection, config_options)) # Registers event handlers
    client.add_cog(CommandHandler(client, db_connection, config_options)) # Registers command handlers

    client.run(config_options['token'])

if __name__ == "__main__":
   try:
      main()
   except KeyboardInterrupt:
      print ("exiting...")
      exit(0)
