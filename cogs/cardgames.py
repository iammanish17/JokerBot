import discord
from discord.ext import commands
from random import sample
import asyncio


class CardGames(commands.Cog):

    def __init__(self, client):
        self.client = client

    def getcard(self, card):
        return [":hearts:", ":diamonds:", ":spades:", ":clubs:"][int(card/13)] + \
               ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"][card % 13]

    def handvalue(self, cards):
        value = 0
        aces = 0
        for card in cards:
            face = self.getcard(card).split(":")[2]
            if face.isdigit():
                value += int(face)
            elif face in ["J", "Q", "K"]:
                value += 10
            else:
                aces += 1
        if aces >= 1 and value <= 11 - aces:
            return 10 + aces + value
        if aces >= 1 and value > 11 - aces:
            return value + aces
        return value

    @commands.cooldown(1, 60, commands.BucketType.channel)
    @commands.command(pass_context=True, name="hilo")
    async def hilo(self, ctx):
        cards = [i for i in range(13)]
        score = 0
        embed = discord.Embed(title="Hi-Lo Cards Game",
                              description="Type `high` to go high, or `low` to go low.",
                              color=discord.Color.blue())
        currentcard = sample(cards, 1)[0]
        nextcard = ""
        gone = [currentcard]
        cards.remove(gone[0])
        embed.add_field(name="Current Card", value=self.getcard(gone[0]))
        embed.add_field(name="Your Score", value=str(score))
        embed.add_field(name="Previous Cards", value="-", inline=False)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        message = await ctx.channel.send(embed=embed)

        async def workout(msg):
            try:
                await msg.delete()
            except Exception:
                pass
            embed.set_field_at(2, name="Previous Cards", value=embed.fields[2].value + " " + self.getcard(gone[-2]),
                               inline=False)
            embed.set_field_at(1, name="Your Score", value=str(score))
            embed.set_field_at(0, name="Current Card", value=self.getcard(nextcard))
            embed.color = discord.Color.green()
            try:
                await message.edit(embed=embed)
            except Exception:
                pass

        def check(msg):
            nonlocal currentcard, cards, gone, score, nextcard
            if msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ["low", "high"]:
                nextcard = sample(cards, 1)[0]
                if nextcard > currentcard and msg.content.lower() == "low" or nextcard < currentcard and \
                        msg.content.lower() == "high":
                    return True
                gone.append(nextcard)
                cards.remove(nextcard)
                score += 1
                currentcard = nextcard
                self.client.loop.create_task(workout(msg))
                if not cards:
                    return True
            return False

        resp = None
        try:
            resp = await self.client.wait_for('message', timeout=150, check=check)
        except asyncio.TimeoutError:
            await ctx.channel.send(ctx.author.mention+", Meh, you've been taking too long to play this game, "
                                                      "and Wumpus has decided that you lost!")
        if resp:
            if not cards:
                embed.description = "Congratulations, you have got a perfect score of 12 and won the game!"
            else:
                embed.color = discord.Color(0XFF0000)
                embed.description = "Game Over! You lost. The next card was: %s" % self.getcard(nextcard)
                ctx.command.reset_cooldown(ctx)
                await message.edit(embed=embed)

    @commands.cooldown(1, 45, commands.BucketType.channel)
    @commands.command(pass_context=True, name="blackjack", aliases=['bj'])
    async def blackjack(self, ctx):
        embed = discord.Embed(title="Blackjack Game",
                              description="Beat the dealer to win! Type `hit` to draw another card, or `stand` to "
                                          "stand with your current hand.",
                              color=discord.Color.blurple())
        cards = [i for i in range(52)]
        player_cards = sample(cards, 2)
        for k in player_cards:
            cards.remove(k)
        value = self.handvalue(player_cards)
        embed.add_field(name="Your cards are",
                        value=" ".join(self.getcard(k) for k in player_cards)+" (%s)" % str(value),
                        inline=False)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        message = await ctx.channel.send(embed=embed)
        resp = None
        if value >= 21:
            resp = True
        else:
            async def edit_hand(msg):
                embed.color = discord.Color(0x663399)
                value = self.handvalue(player_cards)
                embed.set_field_at(0,name="Your cards are",
                                   value=" ".join(self.getcard(k) for k in player_cards)+" (%s)" % str(value),
                                   inline=False)
                try:
                    await message.edit(embed=embed)
                except Exception:
                    pass

            def check(msg):
                nonlocal cards, player_cards
                if msg.author == ctx.author and msg.channel == ctx.channel:
                    if msg.content == "stand":
                        return True
                    if msg.content == "hit":
                        player_cards.append(sample(cards, 1)[0])
                        cards.remove(player_cards[-1])
                        if self.handvalue(player_cards) >= 21:
                            return True
                        self.client.loop.create_task(edit_hand(msg))
                return False

            try:
                resp = await self.client.wait_for("message", timeout=45, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send(ctx.author.mention+", Wumpus is angry that you have been taking too long to play"
                                                          ", and he is saying that you lose. His word is law, alright?")

        if resp:
            ctx.command.reset_cooldown(ctx)
            val = self.handvalue(player_cards)
            embed.set_field_at(0, name="Your cards are",
                               value=" ".join(self.getcard(k) for k in player_cards) + " (%s)" % str(val),
                               inline=False)
            if val > 21:
                embed.color = discord.Color(0xFF0000)
                embed.description = "Game Over! You busted. The Dealer wins."
                await message.edit(embed=embed)
            else:
                dealer_cards = sample(cards, 2)
                for k in dealer_cards:
                    cards.remove(k)
                dealer_val = self.handvalue(dealer_cards)
                while 2 <= dealer_val <= 16:
                    dealer_cards.append(sample(cards, 1)[0])
                    cards.remove(dealer_cards[-1])
                    dealer_val = self.handvalue(dealer_cards)
                if dealer_val > 21 or val > dealer_val:
                    embed.description = "You won! The Dealer busted." if dealer_val > 21 else "You beat the Dealer!"
                    embed.color = discord.Color.green()
                elif dealer_val == val:
                    embed.description = "Looks like it's a draw!"
                    embed.color = discord.Color(0xFFFF00)
                else:
                    embed.description = "Game over! You lost."
                    embed.color = discord.Color(0xFF0000)
                embed.add_field(name="The Dealer's cards are",
                                value=" ".join(self.getcard(k) for k in dealer_cards)+" (%s)" % str(dealer_val),
                                inline=False)
                await message.edit(embed=embed)


def setup(client):
    client.add_cog(CardGames(client))
