from discord.ext import commands
from random import randint, sample, shuffle
from collections import defaultdict
import discord
import asyncio


class WordGames(commands.Cog):

    def __init__(self, client):
        self.client = client
        lines = [line.rstrip('\n') for line in open('searchwords.txt')]
        self.searchwords = defaultdict(list)
        for k in lines:
            self.searchwords[len(k)].append(k)
        self.allwords = [line.rstrip('\n') for line in open('allwords.txt')]

    def wordfill(self, grid, word, direction):
        possible = []
        if direction == 1:
            for i in range(9):
                for j in range(9 - len(word) + 1):
                    next_route = []
                    flag = True
                    for k in range(len(word)):
                        if grid[i][j + k] in [word[k], "*"]:
                            next_route.append((i, j + k))
                        else:
                            flag = False
                            break
                    if flag:
                        possible.append(next_route)

        if direction == 2:
            for i in range(9 - len(word) + 1):
                for j in range(9):
                    next_route = []
                    flag = True
                    for k in range(len(word)):
                        if grid[i + k][j] in [word[k], "*"]:
                            next_route.append((i + k, j))
                        else:
                            flag = False
                            break
                    if flag:
                        possible.append(next_route)

        if direction == 3:
            for i in range(9 - len(word) + 1):
                for j in range(9 - len(word) + 1):
                    next_route = []
                    flag = True
                    for k in range(len(word)):
                        if grid[i + k][j + k] in [word[k], "*"]:
                            next_route.append((i + k, j + k))
                        else:
                            flag = False
                            break
                    if flag:
                        possible.append(next_route)

        return possible

    def generate_grid(self, wordlist):
        wordgrid = []
        skipped = []
        for row in range(9):
            wordgrid.append([])
            for col in range(9):
                wordgrid[row].append("*")
        for word in wordlist:
            word = word.upper()
            routes = self.wordfill(wordgrid, word, randint(1, 3))
            if not routes:
                skipped.append(word)
                continue
            else:
                route = sample(routes, 1)[0]
                for k in range(len(word)):
                    wordgrid[route[k][0]][route[k][1]] = word[k]

        for i in range(9):
            for j in range(9):
                if wordgrid[i][j] == "*":
                    wordgrid[i][j] = chr(randint(65, 90))

        return wordgrid, skipped

    def check_word(self, word, line_grid):
        for i in range(81):
            if line_grid[i] == word[0]:
                that_row = line_grid[9 * int(i / 9):9 * (int(i / 9) + 1)]
                that_col = "".join(line_grid[i % 9 + 9 * k] for k in range(9))
                that_diagonal = "".join(line_grid[i + 10 * k] for k in range(9) if i + 10 * k < 81)
                that_diagonal = that_diagonal[:(9 - i % 9)]
                another_diagonal = "".join(line_grid[i + 8 * k] for k in range(9) if i + 8 * k < 81)
                another_diagonal = another_diagonal[:(1 + i % 9)]
                if word in that_row or word in that_col or word in that_diagonal or word in another_diagonal:
                    return True
        return False

    @commands.cooldown(1, 75, commands.BucketType.channel)
    @commands.command(pass_context=True, name="wordhunt", aliases=['wh'])
    async def wordhunt(self, ctx):
        long_words = sample(self.searchwords[6], randint(1,2)) + sample(self.searchwords[randint(6,8)], randint(1,2))
        other_words = sample(self.searchwords[5], randint(2, 3)) + sample(self.searchwords[4], randint(2, 3))
        wordlist = long_words + other_words
        grid, skipped = self.generate_grid(wordlist)
        linegrid = "".join(r for r in ["".join(p for p in k) for k in grid])
        wordlist = [word for word in wordlist if word not in skipped]
        puzzle_text = ""
        howtoplay = "Find as many words as you can from the grid. Words can be found horizontally, vertically or " \
                    "diagonally, and might also be hidden backwards. You have 75 seconds."
        for rows in grid:
            puzzle_text += "".join(":regional_indicator_"+p.lower()+":" for p in rows) + "\n"
        embed = discord.Embed(title="Word Hunt Game", description=puzzle_text, color=discord.Color.dark_purple())
        embed.add_field(name="How To Play?", value=howtoplay)
        embed.set_footer(text="Requested by "+str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed)

        usedwords, points = [], {}

        async def react(msg):
            try:
                await msg.add_reaction("✅")
            except Exception:
                pass

        def check(msg):
            nonlocal points, usedwords
            if not msg.author.bot and msg.channel == ctx.channel:
                tocheck = msg.content.strip().upper()
                if len(tocheck) <= 9 and tocheck not in usedwords and tocheck.lower() in self.allwords:
                    if self.check_word(tocheck, linegrid) or self.check_word(tocheck[::-1], linegrid):
                        usedwords.append(tocheck)
                        if msg.author.id not in points:
                            points[msg.author.id] = 1
                        else:
                            points[msg.author.id] += 1
                        self.client.loop.create_task(react(msg))
            return False

        try:
            await self.client.wait_for('message', timeout=75, check=check)
        except asyncio.TimeoutError:
            not_found = [word for word in wordlist if word.upper() not in usedwords]
            if not points:
                await ctx.channel.send("Looks like nobody could find a word. That's disappointing! :(\n\n"
                                       "Here are some of the hidden words: "+", ".join(p for p in not_found))
            else:
                top = [sorted(points.values(), reverse=True), sorted(points, key=points.get, reverse=True)]
                top_text = ""
                for i in range(len(top[0])):
                    top_text += "**#"+str(i+1)+" - <@" + str(top[1][i]) + '> (' + str(int(top[0][i])) + ' words)**' + '\n'
                embed = discord.Embed(title="Time's Up!!! Here are the results.", description=top_text,
                                      color=discord.Color.dark_red())
                if not_found:
                    embed.add_field(name="Some hidden words which nobody found", value=", ".join(p for p in not_found),
                                    inline=False)
                embed.set_footer(text="Game started by "+str(ctx.author), icon_url=ctx.author.avatar_url)
                await ctx.channel.send(embed=embed)
                await ctx.channel.send("**:trophy: <@%s> wins the game!**" % str(top[1][0]))

    @commands.cooldown(1, 60, commands.BucketType.channel)
    @commands.command(pass_context=True, name="extremehunt", aliases=['eh'])
    async def extremehunt(self, ctx):
        long_words = sample(self.searchwords[6], randint(1, 2)) + sample(self.searchwords[randint(6, 8)], randint(1, 2))
        other_words = sample(self.searchwords[5], randint(2, 3)) + sample(self.searchwords[4], randint(2, 3))
        wordlist = long_words + other_words
        grid, skipped = self.generate_grid(wordlist)
        linegrid = "".join(r for r in ["".join(p for p in k) for k in grid])
        puzzle_text = ""
        howtoplay = "Find the longest word that you can from the grid. Words can be found horizontally, vertically or " \
                    "diagonally, and might also be hidden backwards. You have 60 seconds."
        for rows in grid:
            puzzle_text += "".join(":regional_indicator_" + p.lower() + ":" for p in rows) + "\n"
        embed = discord.Embed(title="Extreme Hunt Game", description=puzzle_text, color=discord.Color.dark_purple())
        embed.add_field(name="How To Play?", value=howtoplay)
        embed.set_footer(text="Requested by " + str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed)

        async def react(msg):
            try:
                await msg.add_reaction("✅")
            except Exception:
                pass

        curword = ""
        winner = 0

        def check(msg):
            nonlocal curword, winner
            if not msg.author.bot and msg.channel == ctx.channel:
                tocheck = msg.content.strip().upper()
                if len(curword) < len(tocheck) <= 9 and tocheck.lower() in self.allwords:
                    if self.check_word(tocheck, linegrid) or self.check_word(tocheck[::-1], linegrid):
                        curword = tocheck
                        winner = msg.author.id
                        self.client.loop.create_task(react(msg))
            return False

        try:
            await self.client.wait_for('message', timeout=60, check=check)
        except asyncio.TimeoutError:
            if curword == "":
                await ctx.channel.send("Looks like nobody could find a word. That's disappointing! :(")
            else:
                await ctx.channel.send("**Time's up! <@%s> wins the game with the word '%s'.**" % (str(winner), curword))

    @commands.cooldown(1, 30, commands.BucketType.channel)
    @commands.command(pass_context=True, name="scramble", aliases=["wordscramble"])
    async def scramble(self, ctx):
        words_to_choose_from = self.searchwords[6] + self.searchwords[7] + self.searchwords[8] + self.searchwords[9]
        word = sample(words_to_choose_from, 1)[0]
        letters = [letter for letter in word]
        shuffle(letters)
        scrambled_word = "".join(letter for letter in letters)
        desc_text = "".join(":regional_indicator_"+k+":" for k in scrambled_word)
        embed = discord.Embed(title="Word Scramble", description=desc_text, color=discord.Color.blurple())
        embed.add_field(name="How To Play?", value="The letters of a word have been scrambled. Unscramble it and type"
                                                   " the original word. You have 30 seconds.")
        embed.set_footer(text="Game started by "+str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed)

        def check(msg):
            return not msg.author.bot and msg.content.lower().strip() == word and msg.channel == ctx.channel
        resp = None
        try:
            resp = await self.client.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.channel.send("Looks like nobody knew the answer. The original word was **%s**." % word.upper())
        if resp:
            await ctx.channel.send("**Congratulations** %s, you guessed the word correctly: **%s**" %
                                   (resp.author.mention, word.upper()))
            ctx.command.reset_cooldown(ctx)

    @commands.cooldown(1, 900, commands.BucketType.channel)
    @commands.command(pass_context=True, name="passthebomb", aliases=['ptb'])
    async def passthebomb(self, ctx):
        players = []
        msg = await ctx.channel.send(":bomb: **Pass The Bomb** has been started! React with :white_check_mark: to join."
                                     " The bomb will be passed to all the players and they will have 10 seconds to come"
                                     " up with a word, or they will be eliminated. Words cannot be repeated.")
        await msg.add_reaction("✅")

        def check(reaction, user):
            if not user.bot and user.id not in players and str(reaction.emoji) == "✅" and reaction.message.id == msg.id:
                players.append(user.id)
            return False
        try:
            await self.client.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            if len(players) < 2:
                ctx.command.reset_cooldown(ctx)
                await ctx.channel.send("**The game requires at least 2 players to start. Try again!**")
                return
        players = players[:6]
        turn = 0
        two_letter = ['ab', 'ad', 'ag', 'am', 'an', 'ar', 'at', 'ay', 'by', 'do', 'en', 'es', 'et', 'fe', 'it', 'mo',
                      'ma', 'pe', 'py', 're', 'ti', 'us']
        three_letter = ['abs', 'abo', 'aby', 'ace', 'ads', 'ail', 'ant', 'are', 'art', 'ass', 'ave', 'avo', 'bal',
                        'ban', 'bas', 'bar', 'bay', 'beg', 'bis', 'boo', 'bot', 'bra', 'bud', 'bug', 'bus', 'cab',
                        'cap', 'cad', 'cat', 'cel', 'chi', 'cob', 'cog', 'cor', 'cow', 'cry', 'cue', 'cut', 'dab',
                        'dis', 'dit', 'doe', 'dog', 'don', 'dot', 'dry', 'eel', 'eek', 'ego', 'elf', 'eme', 'ems',
                        'end', 'eng', 'ere', 'erg', 'ess', 'eye', 'fee', 'fay', 'fes', 'fig', 'fin', 'fit', 'fro',
                        'fur', 'gad', 'gal',
                        'git', 'hin', 'hit', 'icy', 'iff', 'ill', 'ins', 'its', 'lis', 'lit', 'lot', 'lye', 'oar',
                        'obe', 'oes', 'ole', 'oot', 'ore', 'out', 'pes', 'pie', 'red', 'rot', 'sal', 'sat', 'see',
                        'sip', 'sod', 'sot', 'syn', 'vet', 'yet']
        sub, turn, mode = "", 0, 0
        used = []

        async def play():
            nonlocal sub, turn, mode, used
            sub = sample(two_letter + three_letter, 1)[0]
            mode = randint(0,2)
            text = "Type a word that ends with: **%s**/Type a word that starts with: **%s**/Type a word that " \
                   "contains: **%s**".split("/")[mode]
            text = text.replace("%s", sub.upper())
            await ctx.channel.send("<@"+str(players[turn])+"> You have the :bomb: **Bomb** now. "+text)

            async def reactto(msg):
                try:
                    await msg.add_reaction("✅")
                except Exception:
                    pass

            def checkword(msg):
                if msg.author.id == players[turn]:
                    if msg.content.lower().strip() not in used and msg.content.lower().strip() in self.allwords:
                        content = msg.content.lower().strip()
                        if content.endswith(sub) and mode == 0:
                            used.append(content)
                            self.client.loop.create_task(reactto(msg))
                            return True
                        if content.startswith(sub) and mode == 1:
                            used.append(content)
                            self.client.loop.create_task(reactto(msg))
                            return True
                        if sub in content and mode == 2:
                            used.append(content)
                            self.client.loop.create_task(reactto(msg))
                            return True
                return False
            try:
                await self.client.wait_for('message', timeout=10, check=checkword)
            except asyncio.TimeoutError:
                await ctx.channel.send("The :bomb: **Bomb** exploded! <@%s> has been eliminated." % str(players[turn]))
                players.pop(turn)
            if len(players) == 1:
                ctx.command.reset_cooldown(ctx)
                await ctx.channel.send("**:trophy: <@%s> has survived the bomb and won the game!**" % str(players[0]))
                return
            turn = (turn+1) % len(players)
            self.client.loop.create_task(play())

        self.client.loop.create_task(play())


def setup(client):
    client.add_cog(WordGames(client))
