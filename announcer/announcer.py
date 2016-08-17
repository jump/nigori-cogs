import discord
import os
from discord.ext import commands
from .utils.dataIO import fileIO
from .utils import checks
import datetime
from gtts import gTTS

class Announcer:

    """Announcer users. The more I stare at this word (Announcer) the less it means."""

    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/announcer/Announcer.json"
        self.data_directory = "data/announcer/"

        try:
            self.data = fileIO(data_file,"load")
        except:
            print("Failure to load voice files. Creating new blank data file.")
            self.data = {}
            save()

    async def on_voice_state_update(self, member):
        if member.voice_channel:
            # TODO: get the bot to join the same voice channel
            voice_file = get_user_voice_file(member)

            # get bot to join proper voice channel
            self.bot.join_voice_channel(member.voice_channel)

            voice_client = self.bot.voice_client_in(member.server)

            try:
                voice_client.audio_player.process.kill()
            except AttributeError:
                pass
            except ProcessLookupError:
                pass

            voice_client.create_ffmpeg_player(voice_file, False, options='-b:a 64k -bufsize 64k')
            voice_client.audio_player.volume = self.get_server_settings(member.server)['VOLUME'] / 100
            voice_client.audio_player.start()


    def get_user_voice_file(self, member):
        # load voice file for the user that joined
        if not os.path.isfile(self.data_directory + member.name + ".mp3"):
            voice_file = create_user_voice_file(member)
            self.data[member.name] = voice_file
            save()
            return voice_file

        else:
            voice_file = self.data[member.name]
            return voice_file

    def create_user_voice_file(self, member):
        name = member.name
        voice_audio = gTTS(text=member.name, lang='en')
        voice_file = self.data_directory + member.name + ".mp3"
        voice_audio.save(voice_file)
        return voice_file

def save():
    try:
        fileIO(self.data_file, "save", self.data)
    except:
        print("Error saving! This shouldn't happen.")

def build_folders():
    folders = ("data", "data/Announcer/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def setup(bot):
    build_folders()
    bot.add_cog(Announcer(bot))
