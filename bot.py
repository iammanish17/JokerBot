from discord.ext.commands import Bot, when_mentioned_or
from os import listdir
from os.path import isfile, join
from discord import Game
import json

description = '''Joker Bot'''
cogs_dir = "cogs"

client = Bot(description="Discord Bot by manish17", command_prefix=when_mentioned_or("j!"))
client.remove_command("help")

@client.event
async def on_ready():
    await client.change_presence(activity=Game(name=" with Batman and Wumpus!"))
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

if __name__ == "__main__":
    for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
        try:
            client.load_extension("cogs." + extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.')
            print(str(e))

    with open("config.json", "r") as f:
        data = json.load(f)
        f.close()
    client.run(data["token"])
