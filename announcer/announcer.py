import os
from .utils.dataIO import fileIO
from gtts import gTTS
import asyncio
import discord

__author__ = 'nigori'
__version__ = '0.0.1'


class Announcer:

    """Announcer users. Get the bot to join a channel, then play an MP3."""
    def __init__(self, bot):
        self.bot = bot
        self.data_directory = "data/announcer/"
        self.data = None

        try:
            self.data = fileIO("data/announcer/announcer.json", "load")
        except:
            save(self)

    async def on_voice_state_update(self, before, member):
        # bot should not announce itself when joining a channel
        # so the bot is loop joining the channel, whch is causing the crash.
        print("Grabbed User:%s with id:%s, and the bot id:%s" %
              (member.name, member.id, self.bot.user.id))
        if member.id == self.bot.user.id:
            print("returning early, we detected Harambe joining a channel")
            return
        elif member.voice_channel:
            voice_file = self.get_user_voice_file(member)
            if not voice_file:
                print("failed to get voice file for {}".format(member.name))
                return
            print("got voice file:" + voice_file)
            print(member.name)
            print("self.data: " + str(self.data))

            # get the bot to join the channel
            try:
                await self.bot.join_voice_channel(member.voice_channel)
            except discord.opus.OpusNotLoaded:
                await self.bot.say("Opus is not loaded! Will not work.")
            # attempt to speak the TTS name in channel
            await self.speak_my_child(self, member, voice_file)

    async def speak_my_child(self, member, voice_file):
            voice_client = self.bot.voice_client_in(member.server)

            if voice_client:
                voice_client.create_ffmpeg_player(voice_file, False, options='-b:a 64k -bufsize 64k')
                voice_client.audio_player.volume = self.get_server_settings(member.server)['VOLUME'] / 100
                await voice_client.audio_player.start()
                await asyncio.sleep(6)
                await voice_client.audio_player.stop()
            else:
                print("in speakmychild, don't have a handle to voice client.")

    def get_user_voice_file(self, member):
        # load voice file for the user that joined
        print("attempting to get user voice file for ", member.name)

        if not os.path.isfile(self.data_directory + member.name + ".mp3"):
            voice_file = self.create_user_voice_file(member)
            self.data[member.name] = voice_file
            save(self)
            return voice_file
        elif not member.name in self.data:
            self.data[member.name] = self.data_directory + member.name + ".mp3"
            save(self)
        else:
            voice_file = self.data[member.name]
            return voice_file

    def create_user_voice_file(self, member):
        print("attempting to create user voice file for ", member.name)
        voice_audio = gTTS(text=member.name, lang='en')
        voice_file = self.data_directory + member.name + ".mp3"
        voice_audio.save(voice_file)
        return voice_file

def save(self):
    try:
        fileIO("data/announcer/announcer.json", "save", self.data)
    except:
        print("saving an fresh announcer.json")
        fileIO("data/announcer/announcer.json", "save", {})

def build_folders():
    folders = ("data", "data/announcer/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def setup(bot):
    build_folders()
    bot.add_cog(Announcer(bot))
