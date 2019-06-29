from discord.ext import commands
import discord
from math import ceil
from humanfriendly import format_timespan


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.info = {
            "passthebomb": "Come up with a word quickly, or the bomb will explode on you!",
            "mysticsquare": "Move the tiles in the puzzle and order them from 1-15 to win.",
            "wordhunt": "Find as many words from the grid as you can!",
            "extremehunt": "Find the longest word from the grid to win!",
            "hilo": "Score 12 points and win by guessing if the next card is high/low.",
            "whosthatpokemon": "Guess the pokemon from the image!",
            "blackjack": "Beat the dealer without exceeding 21!",
            "guessthemovie": "Guess the movie from the emojis!",
            "scramble": "Unscramble the word to win!",
            "caption": "Captions any image provided!",
            "help": "Views the list of commands, or info about any command.",
            "ping": "Pong!",
            "invite": "Add me to your server, or join my support server."
        }

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if not isinstance(error, (commands.CommandNotFound, commands.CommandOnCooldown)):
            ctx.command.reset_cooldown(ctx)

        ignored = (commands.CommandNotFound, commands.UserInputError)
        error = getattr(error, 'original', error)
        if isinstance(error, ignored):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            seconds = ceil(error.retry_after)
            towait = format_timespan(seconds)
            await ctx.channel.send("**%s**, You can use this command again after %s." % (ctx.author.name, towait))
        elif isinstance(error, discord.Forbidden) and error.code == 50013:
            if ctx.channel.permissions_for(ctx.guild.me).send_messages:
                await ctx.channel.send("Hey, looks like I don't have proper permissions to run the command. "
                                       "Please make sure I have atleast the following permissions and try again:\n"
                                       "`Send Embed Links`, `Add Reaction`, `Use External Emojis`, `Manage Messages`.")
        else:
            print(error)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        allowed = []
        for channel in guild.channels:
            if channel.permissions_for(guild.me).send_messages and channel.permissions_for(guild.me).embed_links:
                allowed.append(channel)

        if len(allowed) >= 1:
            to_post = allowed[0]
            for channel in allowed:
                if "general" in channel.name:
                    to_post = channel
                    break
            command_list = [k for k in self.info]
            main_help = "\n".join("**j!%s**: %s" % (k, self.info[k]) for k in command_list[:10])
            info_help = "\n".join("**j!%s**: %s" % (k, self.info[k]) for k in command_list[10:])
            embed = discord.Embed(title="JokerBot Help", color=discord.Color.dark_magenta(),
                                  description="Hey there, I am %s! Why so serious? My prefix is **j!**, or you can "
                                              "mention me to use my commands." % guild.me.mention)
            embed.set_author(name=str(guild.me), icon_url=guild.me.avatar_url)
            embed.add_field(name=":video_game: Games and Fun", value=main_help, inline=False)
            embed.add_field(name=":gear: Info Commands", value=info_help, inline=False)
            await to_post.send(embed=embed)

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(pass_context=True)
    async def ping(self, ctx):
        async with ctx.channel.typing():
            await ctx.channel.send("Pong! :white_check_mark:")

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(pass_context=True, name="invite", aliases=['server', 'support', 'about', 'botinfo'])
    async def invite(self, ctx):
        embed = discord.Embed(color=discord.Color.dark_blue(),
                              title="JokerBot Info",
                              description = "Created by **manish#9999** using [discord.py](https://discordpy.readthedocs.io/en/latest/index.html)!"
                                            "\n\n[Add me to your server here!](https://discordapp.com/oauth2/authorize?client_id=592938355818233856&scope=bot&permissions=8)"
                                            "\n[Join my support server here!](https://discord.gg/2ksxEug)\n"
                                            "[View my GitHub repository here!](https://github.com/iammanish17/JokerBot)")
        embed.set_footer(text="Requested by "+str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed)

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(pass_context=True)
    async def help(self, ctx, arg: str = ""):
        if arg == "":
            command_list = [k for k in self.info]
            main_help = "\n".join("**j!%s**: %s" % (k, self.info[k]) for k in command_list[:10])
            info_help = "\n".join("**j!%s**: %s" % (k, self.info[k]) for k in command_list[10:])
            embed = discord.Embed(title="JokerBot Help", color=discord.Color.dark_magenta(),
                                  description="Hey there, I am %s! Why so serious? My prefix is **j!**, or you can "
                                              "mention me to use my commands." % ctx.guild.me.mention)
            embed.set_author(name=str(ctx.guild.me), icon_url=ctx.guild.me.avatar_url)
            embed.set_footer(text="Requested by "+str(ctx.author), icon_url=ctx.author.avatar_url)
            embed.add_field(name=":video_game: Games and Fun", value=main_help, inline=False)
            embed.add_field(name=":gear: Info Commands", value=info_help, inline=False)
            await ctx.channel.send(embed=embed)
        else:
            found = None
            for command in self.client.commands:
                if command.name == arg or arg in command.aliases:
                    found = True
                    break
            if found:
                embed = discord.Embed(title="Help for "+command.name,
                                      description=self.info[command.name],
                                      color=discord.Color.dark_purple())
                syntax_dict = {"caption": "<image-url>", "help": "<command-name (optional)>"}
                embed.add_field(name="Syntax", value="`j!%s %s`" % (command.name,
                                                                  "" if command.name not in syntax_dict else syntax_dict[command.name]))
                if command.aliases:
                    embed.add_field(name="Aliases",
                                    value=", ".join("`j!%s`" % k for k in command.aliases), inline=False)
                embed.set_footer(text="Requested by "+str(ctx.author), icon_url=ctx.author.avatar_url)
                await ctx.channel.send(embed=embed)
            else:
                await ctx.channel.send(ctx.author.name+", No command called `"+arg+"` could be found!")


def setup(client):
    client.add_cog(Help(client))
