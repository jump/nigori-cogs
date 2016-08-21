import discord
import os
from discord.ext import commands
from .utils.dataIO import fileIO
from .utils import checks
import datetime

class Autostatus:

    """ Automatically set the bot's status on startup """

    def __init__(self, bot):
        self.bot = bot
        self.autostatus = {}
        try:
            self.autostatus['startup'] = fileIO("data/autostatus/autostatus.json","load")
        except:
            print("Exception when loading autostatus!")

    @commands.command(pass_context=False, no_pm=False)
    @checks.mod_or_permissions(manage_messages=True)
    async def status(self, newstatus=None):
        if newstatus:
            print(newstatus)
            self.autostatus['startup'] = str(newstatus).strip()
            fileIO("data/autostatus/autostatus.json", "save", self.autostatus)
            await self.bot.change_status(discord.Game(name=newstatus))
        else:
            response = 'Usage: !status "add the status you want here" '
            await self.bot.say(response)

    async def on_ready(self):
        if self.autostatus['startup']:
            await self.bot.change_status(discord.Game(name=self.autostatus['startup']))
        else:
            return

def build_folders():
    folders = ("data", "data/autostatus/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)
    if not os.path.isfile("data/autostatus/autostatus.json"):
        print("creating default autostatus.json...")
        fileIO("data/autostatus/autostatus.json", "save", {})

def setup(bot):
    build_folders()
    bot.add_cog(Autostatus(bot))
