import discord
import os
import datetime
import logging
from discord.ext import commands
from .utils.dataIO import fileIO
from .utils import checks

log = logging.getLogger(__name__)


class Vouch:

    """Vouch users. The more I stare at this word (Vouch) the less it means."""

    def __init__(self, bot):
        self.bot = bot
        try:
            self.vouchers = fileIO("data/vouchers/vouchers.json", "load")
        except:
            log.debug("Exception when loading vouchers!")

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(create_instant_invite=True)
    async def vouch(self, ctx, user: discord.Member=None):
        """Record vouches, when members want to endose non members."""

        if user:
            if user.id == self.bot.user.id:
                user = ctx.message.author
                response = "- thanks for vouching for me, your robot overlord."
                await self.bot.say(user.mention + response)

            elif user.id == ctx.message.author.id:
                response = "- you can't vouch for yourself, you silly goose"
                await self.bot.say(user.mention + response)

            else:
                # see if this author has previously vouched for this user.
                for item in self.vouchers:
                    if item['VOUCHER'] == ctx.message.author.display_name:
                        if item['USER'] == user.display_name:
                            response = " you already vouched for this user"
                            await self.bot.say(ctx.message.author.mention +
                                               response)
                            return

                # check if USER has already been vouched, record the new name
                for item in self.vouchers:
                    if item['USER'] == user.display_name:
                        if not item['VOUCHER'] == \
                                ctx.message.author.display_name:
                            # case: we have a USER who has already been vouched
                            # vouched for again, by a different discord member
                            item['VOUCHER'] = item['VOUCHER'] + ", " + \
                                    ctx.message.author.display_name
                            fileIO("data/vouchers/vouchers.json", "save",
                                   self.vouchers)
                            await self.bot.say(ctx.message.author.mention +
                                               ", recorded.")
                            await self.bot.say(user.display_name +
                                               " now has multple vouches.")
                            return

                # record the vouching
                self.vouchers.append({"VOUCHER": ctx.message.author.display_name,
                                      "USER": user.display_name, "ID": user.id,
                                      "DATE": str("{:%B %d, %Y}".format(
                                                   datetime.datetime.now()))})
                fileIO("data/vouchers/vouchers.json", "save", self.vouchers)
                response = " - your voucher for " + user.mention + \
                           " has been recorded."
                await self.bot.say(ctx.message.author.mention + response)

        else:
            response = "Usage: !vouch <user>"
            await self.bot.say(response)

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def showvouches(self):
        if self.vouchers:
            for item in self.vouchers:
                await self.bot.say(item['VOUCHER'] + " vouched for " +
                                   item['USER'] + " @ " + item['DATE'])
        else:
            response = "There are no user vouchers."
            await self.bot.say(response)

    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def clearvouches(self):
        self.vouchers.clear()
        fileIO("data/vouchers/vouchers.json", "save", self.vouchers)
        await self.bot.say("Existing vouchers have been cleared.")


def build_folders():
    folders = ("data", "data/vouchers/")
    for folder in folders:
        if not os.path.exists(folder):
            log.debug("Creating " + folder + " folder...")
            os.makedirs(folder)
    if not os.path.isfile("data/vouchers/vouchers.json"):
        log.debug("creating default vouchers.json...")
        fileIO("data/vouchers/vouchers.json", "save", [])


def setup(bot):
    build_folders()
    bot.add_cog(Vouch(bot))
