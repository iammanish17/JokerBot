from discord.ext import commands
import json
from random import randint, sample
import discord
import asyncio


class Pokemon(commands.Cog):

    def __init__(self, client):
        self.client = client
        with open("pokemon.json", "r") as f:
            self.pokemon_data = json.load(f)
            f.close()
        self.total = len(self.pokemon_data)

    @commands.cooldown(1, 20, commands.BucketType.user)
    @commands.command(pass_context=True, name="whosthatpokemon", aliases=["pokemon", "wtp"])
    async def whosthatpokemon(self, ctx):
        number = randint(1, self.total)
        name = self.pokemon_data[str(number)]
        img_url = "https://assets.pokemon.com/assets/cms2/img/pokedex/full/{}.png".format(
            "0" * (3 - len(str(number))) + str(number))
        hint_1 = "".join([c if not c.isalnum() else "*" for c in name])
        letters = [i for i in range(len(name)) if name[i].isalnum()]
        to_delete = set(sample(range(len(letters)), int(len(letters)/2)))
        letters = [x for i, x in enumerate(letters) if i not in to_delete]
        hint_2 = "".join("*" if k in letters else name[k] for k in range(len(name)))
        embed = discord.Embed(title="Who's That Pokémon!", color=discord.Color.dark_blue())
        embed.set_image(url=img_url)
        embed.add_field(name="Hint 1", value="`"+hint_1+"`")
        embed.add_field(name="Time", value="20 seconds")
        embed.set_footer(text="To answer, simply type the name of the pokemon in chat!", icon_url=ctx.author.avatar_url)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        message = await ctx.channel.send(embed=embed)

        async def second():
            await asyncio.sleep(10)
            if message:
                embed.set_field_at(index=0, name="Hint 2", value='`' + hint_2 + '`')
                embed.set_field_at(index=1, name="Time", value="10 seconds")
                await message.edit(embed=embed)

        asyncio.ensure_future(second())

        def check(msg):
            return not msg.author.bot and msg.content.strip().lower().replace(" ", "") == name.lower().replace(" ", "") and msg.channel == ctx.channel

        resp = None
        try:
            resp = await self.client.wait_for('message', timeout=20, check=check)
        except asyncio.TimeoutError:
            await ctx.channel.send("Time's up! The pokemon was **%s**." % name)

        if resp:
            ctx.command.reset_cooldown(ctx)
            try:
                await resp.add_reaction("✅")
            except Exception:
                pass
            embed = discord.Embed(title="Who's That Pokémon!",
                                  description="Congratulations "+resp.author.mention+"! You've given the correct answer!"
                                                                                     " The pokemon was **%s**." % name,
                                  color=discord.Color.green())
            embed.set_thumbnail(url=img_url)
            embed.set_footer(text="Game started by "+str(ctx.author), icon_url=ctx.author.avatar_url)
            message = await message.edit(embed=embed)


def setup(client):
    client.add_cog(Pokemon(client))
