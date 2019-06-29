from discord.ext import commands
import json
import discord
from random import shuffle
import asyncio
from time import time
from humanfriendly import format_timespan


class Mystic(commands.Cog):
    def __init__(self, client):
        self.client = client
        with open("config.json", "r") as f:
            data = json.load(f)
            f.close()
        self.emojis = {
            1: ":one:",
            2: ":two:",
            3: ":three:",
            4: ":four:",
            5: ":five:",
            6: ":six:",
            7: ":seven:",
            8: ":eight:",
            9: ":nine:",
            10: ":keycap_ten:",
            11: data["emojis"]["11"],
            12: data["emojis"]["12"],
            13: data["emojis"]["13"],
            14: data["emojis"]["14"],
            15: data["emojis"]["15"],
            16: ":white_large_square:"
        }

    @commands.cooldown(1, 45, commands.BucketType.user)
    @commands.command(pass_context=True, name="mysticsquare", aliases=["15puzzle", "slidepuzzle"])
    async def mysticsquare(self, ctx):

        def generate_map():
            map = [i+1 for i in range(15)]
            shuffle(map)
            inv_count = 0
            for i in range(15):
                for j in range(i + 1, 15):
                    if map[i] > map[j]:
                        inv_count += 1
            map.append(16)
            if inv_count % 2 == 1:
                map[0], map[1] = map[1], map[0]
            gamemap = []
            for i in range(4):
                gamemap.append([])
                for n in range(4):
                    gamemap[i].append(map[4*i+n])
            return gamemap

        def print_board(gamemap):
            return "\n".join("".join(self.emojis[p] for p in k) for k in gamemap)

        def get_position(search, gamemap):
            position = 0
            for rows in gamemap:
                for row in rows:
                    if row == search:
                        return position
                    position += 1

        def match_count(gamemap):
            count, pos = 0, 1
            for rows in gamemap:
                for row in rows:
                    if row == pos:
                        count += 1
                    pos += 1
            return count

        embed = discord.Embed(title="Mystic Square",
                              description="A game of **Mystic Square** has been started!\n\n**• The objective is to "
                                          "arrange the tiles in increasing order from 1-15 row-wise.\n• You can react "
                                          "with the corresponding emojis to move a tile in the direction shown by that "
                                          "emoji.\n• The tiles can only move to the place which is empty "
                                          "(shown by the white square).\n• You can quit anytime by reacting with "
                                          "the cross mark emoji :x:.**",
                              color=discord.Color.blue())
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed)
        await asyncio.sleep(3)

        gamemap = generate_map()
        moves = 0
        message = await ctx.channel.send(print_board(gamemap))
        await message.add_reaction("◀")
        await message.add_reaction("▶")
        await message.add_reaction("🔼")
        await message.add_reaction("🔽")
        await message.add_reaction("❌")
        start_time = time()

        async def edit_msg(reaction):
            await message.edit(content=print_board(gamemap))
            try:
                await message.remove_reaction(reaction.emoji, ctx.author)
            except Exception:
                pass

        def check(reaction, user):
            nonlocal gamemap, moves
            if user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in "◀▶🔼🔽":
                emoji = str(reaction.emoji)
                empty_pos = get_position(16, gamemap)
                if emoji == "◀" and empty_pos not in [3, 7, 11, 15]:
                    tile_pos = empty_pos + 1
                    gamemap[int(tile_pos/4)][tile_pos % 4], gamemap[int(empty_pos/4)][empty_pos % 4] = \
                        gamemap[int(empty_pos/4)][empty_pos % 4], gamemap[int(tile_pos/4)][tile_pos % 4]
                elif emoji == "▶" and empty_pos not in [0, 4, 8, 12]:
                    tile_pos = empty_pos - 1
                    gamemap[int(tile_pos/4)][tile_pos % 4], gamemap[int(empty_pos/4)][empty_pos % 4] = \
                        gamemap[int(empty_pos/4)][empty_pos % 4], gamemap[int(tile_pos/4)][tile_pos % 4]
                elif emoji == "🔼" and empty_pos not in [12, 13, 14, 15]:
                    tile_pos = empty_pos + 4
                    gamemap[int(tile_pos / 4)][tile_pos % 4], gamemap[int(empty_pos/4)][empty_pos % 4] = \
                        gamemap[int(empty_pos/4)][empty_pos % 4], gamemap[int(tile_pos / 4)][tile_pos % 4]
                elif emoji == "🔽" and empty_pos not in [0, 1, 2, 3]:
                    tile_pos = empty_pos - 4
                    gamemap[int(tile_pos / 4)][tile_pos % 4], gamemap[int(empty_pos/4)][empty_pos % 4] = \
                        gamemap[int(empty_pos/4)][empty_pos % 4], gamemap[int(tile_pos / 4)][tile_pos % 4]
                else:
                    return False
                moves += 1
                self.client.loop.create_task(edit_msg(reaction))
                if match_count(gamemap) >= 15:
                    return True
            elif user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) == "❌":
                return True

            return False

        resp = None
        try:
            resp = await self.client.wait_for('reaction_add', timeout=1200, check=check)
        except asyncio.TimeoutError:
            await ctx.channel.send(ctx.author.mention+" Hey, you're out of time now! Game over!")

        if resp:
            end_time = time()
            time_taken = format_timespan(int(end_time - start_time))
            matches = match_count(gamemap)
            stat_text = "**Moves made:** %s\n**Time taken:** %s\n**Percentage completion:** %s" % (str(moves),
                                                                                                   time_taken,
                                                                                                   str(round(matches*100/16, 2)))

            desc_text = "You decided to quit the game."
            if matches >= 15:
                desc_text = "**Congratulations** %s, you have finished the puzzle successfully and **won** the game!" %\
                       ctx.author.mention

            embed = discord.Embed(title="Game Over",
                                  description=desc_text,
                                  color=discord.Color.green() if matches >= 15 else discord.Color.red())
            embed.add_field(name="Stats", value=stat_text, inline=False)
            embed.set_footer(text="Game started by "+str(ctx.author), icon_url=ctx.author.avatar_url)
            await ctx.channel.send(embed=embed)


def setup(client):
    client.add_cog(Mystic(client))
