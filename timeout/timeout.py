import discord
import asyncio
import logging
from discord.ext import commands
from .utils import checks
from datetime import datetime

log = logging.getLogger(__name__)


class Timeout:

    """If a user spamming in chat, autokick. Also provide ability
       for admins to be able to give someone a timeout, globally
       muting and deafening users """

    def __init__(self, bot):
        self.bot = bot

        # number of messages RX before considering it spam
        self.RX_MESSAGE_THRESHOLD = 5
        # delta between messages before considering it spam
        self.RX_MESSAGE_DELTA_THRESHOLD = 1.5

        self.message_history = {}
        self.spam_levels = {}
        self.shitlist = []
        self.mutelist = {}

    @commands.command(pass_context=False)
    @checks.mod_or_permissions(kick_members=True)
    async def spam(self, command=None):
        if command == "show":
            if self.shitlist:
                for item in self.shitlist:
                    message = item + " is on the shitlist."
                    await self.bot.say(message)
            else:
                response = "There is nobody on the shitlist."
                await self.bot.say(response)

        elif command == "clear":
            self.shitlist.clear()
            await self.bot.say("The shitlist has been emptied.")

        else:
            return

    @commands.command(pass_context=False)
    @checks.mod_or_permissions(kick_members=True)
    async def timeout(self, member: discord.Member=None, minutes=None):
        if member and not minutes:
            try:
                await self.bot.server_voice_state(
                      member, mute=True, deafen=True)
                timestamp = datetime.now().timestamp()
                self.mutelist[member.id] = timestamp
                message = "Muting {} for default time of 3 minutes.".format(
                           member.display_name)
                await self.bot.say(message)
                await self.sleep_timer(member, 3)
            except:
                pass
        elif member and minutes:
            await self.bot.server_voice_state(member, mute=True, deafen=True)
            timestamp = datetime.now().timestamp()
            self.mutelist[member.id] = timestamp
            message = "Muting {} for specified time of {} minutes.".format(
                       member.display_name, minutes)
            await self.bot.say(message)
            await self.sleep_timer(member, minutes)

    async def sleep_timer(self, member: discord.Member=None, time=None):
        if time:
            minutes = int(time)
            await asyncio.sleep(minutes)
            await self.unmute_member(member)

    @commands.command(pass_context=False)
    @checks.mod_or_permissions(kick_members=True)
    async def unmute_member(self, member: discord.Member=None):
        await self.bot.server_voice_state(member, mute=False, deafen=False)
        self.mutelist.pop(member.id, None)
        message = "{} is now unmuted".format(member.display_name)
        await self.bot.say(message)

    async def on_message(self, message):
        timestamp = datetime.now().timestamp()
        author = message.author.display_name

        # don't detect bot messages as spam
        if message.author.id == self.bot.user.id:
            return

        # if it's the user's first message, add a timestamp
        # otherwise if we have an entry for the user, merge the new message

        if not self.message_history:
            self.message_history[author] = [timestamp]
        elif author not in self.message_history:
            self.message_history[author] = [timestamp]
        else:
            self.message_history[author] = self.message_history[author] \
                                                          + [timestamp]
            is_spam = self.check_for_spam(author)
            if is_spam:
                self.shitlist.append(author)
                self.message_history[author] = []
                self.spam_levels[author] = 1
                try:
                    await self.bot.kick(message.author)
                    m = "Spam detected from " + author \
                        + ". Silencing this filthy peasant."
                    await self.bot.send_message(message.channel, m)
                except discord.errors.Forbidden:
                    pass

    def check_for_spam(self, author):
        message_timestamps = self.message_history[author]
        num_messages = len(message_timestamps)

        log.debug("num messages =", num_messages)

        # if they haven't sent enough messages total to be considered spam,
        # we can stop right here
        if num_messages < self.RX_MESSAGE_THRESHOLD:
            return

        # compare self.RX_MESSAGE_THRESHOLD total messages from the message
        # history. if enough flags found for RX Messages (sent too fast),
        # globally mute the user for 5 minutes by default.
        if author in self.spam_levels:
            spamlevel = self.spam_levels[author]
        else:
            spamlevel = 1

        log.debug("num messages = ", num_messages)
        log.debug("spam level = ", spamlevel)

        for i in range(0, num_messages-1, 1):
            try:
                if message_timestamps[i+1] - message_timestamps[i] \
                        <= self.RX_MESSAGE_DELTA_THRESHOLD:
                    spamlevel += 1
            except:
                pass

        self.spam_levels[author] = spamlevel

        if self.spam_levels[author] >= self.RX_MESSAGE_THRESHOLD:
            message = "spam detected from [" + author + "], spamlevel=" \
                        + str(spamlevel)
            log.debug(message)
            return True

        return False


def setup(bot):
    bot.add_cog(Timeout(bot))
