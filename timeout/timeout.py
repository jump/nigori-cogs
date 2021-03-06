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
        self.RX_MESSAGE_THRESHOLD = 7

        # spamlevel before warning
        self.RX_MESSAGE_WARNING_THRESHOLD = 4

        # delta between messages before considering it spam
        self.RX_MESSAGE_DELTA_THRESHOLD = 1.25

        # delta between messages before we reset the spam counter
        self.RX_MESSAGE_RESET_THRESHOLD = 5

        self.message_history = {}
        self.spam_levels = {}
        self.shitlist = []
        self.mutelist = {}

        # a whitelist for discord accounts to avoid timeouts
        self.whitelist = []
        self.whitelist.append(self.bot.user.id)

        # whitelist the Rhythm bot ID
        self.whitelist.append("235088799074484224")

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
    async def immunity(self, member: discord.Member = None):
        if member:
            try:
                await self.whitelist.append(member.id)
                message = "Added {} to whitelist.".format(member.display_name)
                await self.bot.say(message)
            except Exception as e:
                pass

    @commands.command(pass_context=False)
    @checks.mod_or_permissions(kick_members=True)
    async def showimmunity(self):
        if self.whitelist:
            for item in self.whitelist:
                message = item + " is on the whitelist."
                await self.bot.say(message)

    @commands.command(pass_context=False)
    @checks.mod_or_permissions(kick_members=True)
    async def timeout(self, member: discord.Member = None, minutes=None):
        if member and not minutes:
            try:
                await self.bot.server_voice_state(member, mute=True, deafen=True)
                timestamp = datetime.now().timestamp()
                self.mutelist[member.id] = timestamp
                message = "Muting {} for default time of 3 minutes.".format(member.display_name)
                await self.bot.say(message)
                await self.sleep_timer(member, 3)
            except Exception as e:
                pass
        elif member and minutes:
            await self.bot.server_voice_state(member, mute=True, deafen=True)
            timestamp = datetime.now().timestamp()
            self.mutelist[member.id] = timestamp
            message = "Muting {} for specified time of {} minutes.".format(member.display_name, minutes)
            await self.bot.say(message)
            await self.sleep_timer(member, minutes)

    async def sleep_timer(self, member: discord.Member = None, time=None):
        if time:
            minutes = int(time)
            await asyncio.sleep(minutes)
            await self.unmute_member(member)

    @commands.command(pass_context=False)
    @checks.mod_or_permissions(kick_members=True)
    async def unmute_member(self, member: discord.Member = None):
        await self.bot.server_voice_state(member, mute=False, deafen=False)
        self.mutelist.pop(member.id, None)
        message = "{} is now unmuted".format(member.display_name)
        await self.bot.say(message)

    async def on_message(self, message):
        timestamp = datetime.now().timestamp()
        author = message.author.display_name

        # don't detect bot messages as spam
        if message.author.id in self.whitelist:
            return

        # if it's the user's first message, add a timestamp
        # otherwise if we have an entry for the user, merge the new message

        if not self.message_history:
            self.message_history[author] = [timestamp]
        elif author not in self.message_history:
            self.message_history[author] = [timestamp]
        else:
            self.message_history[author] = self.message_history[author] + [timestamp]
            self.reset_if_needed(author)
            is_spam = self.check_for_spam(author)
            need_warning = self.check_for_warning(author)

            if is_spam:
                self.shitlist.append(author)
                self.message_history[author] = []
                self.spam_levels[author] = 1
                try:
                    await self.bot.kick(message.author)
                    m = "TRIGGERED! Spam detected from " + author \
                        + ". Silencing this filthy peasant."
                    await self.bot.send_message(message.channel, m)
                except discord.errors.Forbidden:
                    pass

            if need_warning:
                try:
                    m = message.author.mention + " TRIGGER WARNING! " + \
                        " I am literally shaking, please stop spamming " \
                        + "the channel."
                    await self.bot.send_message(message.channel, m)
                except Exception as e:
                    pass

    def check_for_warning(self, author):
        if author in self.spam_levels:
            if self.spam_levels[author] >= self.RX_MESSAGE_WARNING_THRESHOLD:
                return True

        return False

    def reset_if_needed(self, author):
        message_timestamps = self.message_history[author]
        num_messages = len(message_timestamps)

        # need to check the delta between very latest message
        # and the message just before that one
        if author in self.spam_levels:
            if num_messages > 1:
                if message_timestamps[num_messages-1] - \
                   message_timestamps[num_messages-2] >= \
                   self.RX_MESSAGE_RESET_THRESHOLD:
                    self.spam_levels[author] = 1
                    self.message_history[author] = []

    def check_for_spam(self, author):
        message_timestamps = self.message_history[author]
        num_messages = len(message_timestamps)

        log.debug("num messages =", num_messages)
        authorInSpam = False

        # if they haven't sent enough messages total to be considered spam,
        # we can stop right here
        if num_messages < self.RX_MESSAGE_THRESHOLD:
            return False

        # compare self.RX_MESSAGE_THRESHOLD total messages from the message
        # history. if enough flags found for RX Messages (sent too fast),
        # globally mute the user for 5 minutes by default.
        if author in self.spam_levels:
            spamlevel = int(self.spam_levels[author])
            authorInSpam = True
        else:
            spamlevel = 1

        log.debug("num messages = ", num_messages)
        log.debug("spam level = ", spamlevel)

        for i in range(0, num_messages - 1, 1):
            try:
                if message_timestamps[i + 1] - message_timestamps[i] \
                        <= self.RX_MESSAGE_DELTA_THRESHOLD:
                    spamlevel += 1
            except Exception as e:
                pass

        self.spam_levels[author] = spamlevel

        if authorInSpam and int(self.spam_levels[author]) >= self.RX_MESSAGE_THRESHOLD:
            message = "spam detected from [" + author + "], spamlevel=" + str(spamlevel)
            log.debug(message)
            return True

        return False


def setup(bot):
    bot.add_cog(Timeout(bot))
