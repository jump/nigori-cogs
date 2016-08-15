import discord
import os
from discord.ext import commands
from .utils import checks
from datetime import datetime

class Timeout:

    """If a user is spamming in a chat channel, then lets give them a timeout"""

    def __init__(self, bot):
        self.bot = bot
        self.RX_MESSAGE_THRESHOLD = 5           # number of messages rx before consider spam
        self.RX_MESSAGE_DELTA_THRESHOLD = 1.5   # messages rx with 1.5 or less seconds between
        self.message_history = {}
        self.spam_levels = {}
        self.shitlist = []

    @commands.command(pass_context=True)
    @checks.mod_or_permissions(kick_members=True)
    async def timeout(self, ctx, command):
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
        elif not author in self.message_history:
            self.message_history[author] = [timestamp]
        else:
            self.message_history[author] = self.message_history[author] + [timestamp]
            is_spam = self.check_for_spam(author)
            if is_spam:
                self.shitlist.append(author)
                self.message_history[author] = []
                self.spam_levels[author] = 1
                try:
                    await self.bot.kick(message.author)
                    m = "Spam detected from " + author + ". Silencing this filthy peasant."
                    await self.bot.send_message(message.channel, m)
                except discord.errors.Forbidden:
                    pass
                    #await self.bot.send_message(message.channel, "I'm not allowed to do that.")

        # once we get here, we should have a dictionary mapping author names
        # which produces keys that are lists of timestamps corresponding to when
        # they sent messages.

    def check_for_spam(self, author):
        message_timestamps = self.message_history[author]
        num_messages = len(message_timestamps)

        print("num messages =", num_messages)

        # if they haven't sent enough messages total to be considered spam,
        # we can stop right here
        if num_messages < self.RX_MESSAGE_THRESHOLD:
            return

        # compare self.RX_MESSAGE_THRESHOLD total messages from the message history
        # if enough flags found for RX Messages (sent too fast), globally
        # mute the user for 5 minutes.
        if author in self.spam_levels:
            spamlevel = self.spam_levels[author]
        else:
            spamlevel = 1

        print("num messages = ", num_messages)
        print("spam level = ", spamlevel)

        for i in range (0, num_messages-1,1):
            try:
                if message_timestamps[i+1] - message_timestamps[i] <= self.RX_MESSAGE_DELTA_THRESHOLD:
                    spamlevel += 1
            except:
                pass

        self.spam_levels[author] = spamlevel

        if self.spam_levels[author] >= self.RX_MESSAGE_THRESHOLD:
            message = "spam detected from [" + author + "], spamlevel=" + str(spamlevel)
            print(message)
            return True

        return False

def setup(bot):
    bot.add_cog(Timeout(bot))
