from discord.ext import commands
import discord
from captionbot import CaptionBot
import functools


class Caption(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(pass_context=True)
    async def caption(self, ctx, *, text: str = ""):
        url = ""
        if text:
            url = text
        else:
            if len(ctx.message.attachments) > 0:
                url = ctx.message.attachments[0].url
        if not url:
            await ctx.channel.send(ctx.author.mention + " The correct syntax is: `j!caption <image-url>`.")
        else:
            def captionimage(url):
                c = CaptionBot()
                return c.url_caption(url)
            thing = functools.partial(captionimage, url)
            ptext = await self.client.loop.run_in_executor(None, thing)
            if ptext == "I really can't describe the picture 😳":
                await ctx.channel.send(ctx.author.mention+" No image was found in input.")
            else:
                embed = discord.Embed(title=ptext, color=discord.Color.dark_purple())
                embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
                embed.set_image(url=url)
                embed.set_footer(text="Image captioned with captionbot.ai!")
                await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Caption(client))
