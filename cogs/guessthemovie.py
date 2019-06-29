from discord.ext import commands
import json
from random import sample
import asyncio


class Movie(commands.Cog):
    def __init__(self, client):
        self.client = client
        with open("emojimovie.json", "r") as f:
            self.data = json.load(f)
            f.close()

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(pass_context=True, name="guessthemovie", aliases=['gtm'])
    async def guessthemovie(self, ctx):
        emoji = sample([k for k in self.data], 1)[0]
        movie = self.data[emoji]
        await ctx.channel.send("Guess the movie:\n%s" % emoji)

        def check(msg):
            return not msg.author.bot and \
                   "".join(k for k in msg.content.lower() if k.isalnum()) == "".join(k for k in movie.lower()
                                                                                        if k.isalnum()) and msg.channel == ctx.channel
        try:
            resp = await self.client.wait_for("message", timeout=30, check=check)
            await ctx.channel.send("That's right, %s! You've guessed the movie correctly: **%s**." %
                                   (resp.author.mention, movie))
            ctx.command.reset_cooldown(ctx)
        except asyncio.TimeoutError:
            await ctx.channel.send("Looks like nobody knew the answer. The movie was **%s**." % movie)

        
def setup(client):
    client.add_cog(Movie(client))
