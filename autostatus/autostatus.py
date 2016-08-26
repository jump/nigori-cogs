import discord
import os
import logging
from discord.ext import commands
from .utils.dataIO import fileIO
from .utils import checks

log = logging.getLogger(__name__)


class Autostatus:

    """ Automatically set the bot's status on startup """

    def __init__(self, bot):
        self.bot = bot
        try:
            self.autostatus = fileIO("data/autostatus/autostatus.json", "load")
            self.bot.loop.create_task(self.on_load())
        except:
            log.debug("Exception when loading autostatus!")

    @commands.command(pass_context=False, no_pm=False)
    @checks.mod_or_permissions(manage_messages=True)
    async def status(self, newstatus=None):
        if newstatus:
            self.autostatus['startup'] = str(newstatus).strip()
            fileIO("data/autostatus/autostatus.json", "save", self.autostatus)
            await self.bot.change_status(discord.Game(name=newstatus))
        else:
            response = 'Usage: !status "add the status you want here"'
            if self.autostatus:
                log.debug("current autostatus: " + str(self.autostatus))
            await self.bot.say(response)

    async def on_ready(self):
        await self.bot.wait_until_ready()
        if self.autostatus['startup']:
            log.debug("attempting to set the status to {}".format(
                   self.autostatus['startup']))
            await self.bot.change_status(discord.Game(
                  name=self.autostatus['startup']))
        else:
            return


def build_folders():
    folders = ("data", "data/autostatus/")
    for folder in folders:
        if not os.path.exists(folder):
            log.debug("Creating " + folder + " folder...")
            os.makedirs(folder)
    if not os.path.isfile("data/autostatus/autostatus.json"):
        log.debug("creating default autostatus.json...")
        fileIO("data/autostatus/autostatus.json", "save", {})


def setup(bot):
    build_folders()
    bot.add_cog(Autostatus(bot))
