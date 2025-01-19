import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import yt_dlp
import asyncio
import logging

# Suppress discord.player error messages
discord_logger = logging.getLogger('discord.player')
#discord_logger.setLevel(logging.CRITICAL)  # Suppresses ERROR logs

load_dotenv()
TOKEN: str = os.getenv('DISCORD_TOKEN')

intents: discord.Intents = discord.Intents.default()
intents.message_content = True

# Set up the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -timeout 600',
    'options': '-vn',
    'executable': r'C:\Users\Mokui\Documents\ffmpeg-2025-01-02-git-0457aaf0d3-essentials_build\bin\ffmpeg.exe',
}

# YTDL options
YDL_OPTIONS = {
    'format': 'bestaudio', 
    'noplaylist': 'True',
    'retries': 3,
    'extract_flat': True,  # Don't download the full video, just extract info
    'geo_bypass': True,
    'source_address': '0.0.0.0',
    'extractaudio': True,  # Only extract audio,
    'quiet': False,
    'ignoreerrors': True,
    'timeout': 600,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'webm',  # Or use 'opus' if preferred
        'preferredquality': '192',
    }]
}

# Update YDL_OPTIONS to accommodate playlist download specifics
playlist_YDL_OPTIONS = {
    'format': 'bestaudio',  # Best audio format
    'noplaylist': False,  # Allow playlist processing
    'retries': 3,
    'quiet': True,
    'extract_flat': True,  # Don't download the full video, just extract info
    'geo_bypass': True,
    'source_address': '0.0.0.0',
    'extractaudio': True,  # Only extract audio,
    'ignoreerrors': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'webm',  # Or use 'opus' if preferred
        'preferredquality': '192',
    }]
}

# Track the current voice client and the playing queue
voice_client = None
song_queue = []

# Command to join a voice channel
@bot.command(name="join")
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("Comment y va mon copaing?")
    else:
        await ctx.send("Entres dans le discord d'abord, tié un fou toi!")

# Command to leave a voice channel
@bot.command(name="leave")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Azy je trace, des poutous partout")
    else:
        await ctx.send("Jsuis meme pas là mon gâté!")

# Command to play audio from YouTube
@bot.command(name="play")
async def play(ctx, url: str):
    global voice_client
    if ctx.voice_client is None:
        if ctx.author.voice:
            voice_client = await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Entres dans le discord d'abord, tié un fou toi!")
            return
    else:
        voice_client = ctx.voice_client

    if voice_client.is_playing():
        voice_client.stop()
    
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get("url")

            # Attempt to play the audio using FFmpegOpusAudio
            try:
                source = await discord.FFmpegOpusAudio.from_probe(audio_url, **FFMPEG_OPTIONS)
                voice_client.play(source, after=lambda e: print(f"Finito: {e}"))
                await ctx.send(f"Oh cong, j'envoi la musique là: {info['title']}")
            except Exception as ffmpeg_error:
                # Fallback: Retry with basic FFmpegAudio
                await ctx.send("Ca bug là mon couz, avec le probe FFmpeg. j'essaye un truc...")
                source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
                voice_client.play(source, after=lambda e: print(f"Finito: {e}"))
                await ctx.send(f"Fallback réussi. maintenant jlis: {info['title']}")

    except Exception as e:
        await ctx.send(f"Ayaya y'a un problème mon copaing: {str(e)}")

# Command to play audio from a YouTube Playlist
@bot.command(name="playlist")
async def playlist(ctx, url: str):
    global voice_client, song_queue
    if voice_client is None:
        if ctx.author.voice:
            voice_client = await ctx.author.voice.channel.connect()
        else:
            await ctx.send("Entres dans le discord d'abord, tié un fou toi!")
            return
        
    with yt_dlp.YoutubeDL(playlist_YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                # Filter out unavailable videos (hidden or blocked)
                valid_entries = [entry for entry in info['entries'] if entry.get('available', True)]
                
                for entry in valid_entries:
                    song_queue.append(entry['url'])
                await ctx.send(f"Oké tranquille, je t'ai mis {len(valid_entries)} sons dans ta playlist, installes-toi le sang de ma veine.")
                await next(ctx)
            else:
                await ctx.send("Ya R, nada, que dalle, rien trouvé. Bisous")
        except Exception as e:
            await ctx.send(f"Azy ya un probleme: {str(e)}")

# Function to play the next song in the queue
async def next(ctx):
    global voice_client, song_queue
    if song_queue:
        if not voice_client.is_playing():
            song_url = song_queue.pop(0)
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                try:
                    info = ydl.extract_info(song_url, download=False)
                    url2 = info['url']
                    source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)

                    # Play the song
                    voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(next(ctx), bot.loop))
                    await ctx.send(f"Now playing: {info['title']}")
                except yt_dlp.DownloadError as e:
                    # Handle video unavailability and skip to the next song
                    await ctx.send(f"Il m'a saoulé j'ai viré ce son la: {song_url} , mon couz'")
                    await next(ctx)  # Continue to the next song
                except Exception as e:
                    # If another error occurs, skip it and continue with the next song
                    await ctx.send(f"Ca bug là non?: {str(e)}")
                    await next(ctx)  # Continue to the next song
    else:
        await ctx.send("C'est finit mon gâté, tu veux plus de sons? BAH TU DEMANDES VOILAAA")

# Command to next the song
@bot.command(name="next")
async def nextsong(ctx):
    global song_queue, voice_client
    if song_queue:
        # Stop the current song
        voice_client.stop()
        # Play the next song in the queue
        await next(ctx)
        await ctx.send("Okay, prochain Son, mon gadjo le sang")
    else:
        await ctx.send("J'ai que tchi. Plus rien mon gars")

# Command to pause or resume the song
@bot.command(name="pause")
async def pause(ctx):
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Oké j'arrête?")
    else:
        await ctx.send("Ya rien qui joue là, tié con ou quoi?")

@bot.command(name="resume")
async def resume(ctx):
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Ah oké je remet alors mon frerot.")
    else:
        await ctx.send("Y'a rien a remettre, y'a pas de son mon gâté. LES OREILLES C'EST COMME LE CUL...")

# Command to stop the current song and clear the playlist
@bot.command(name="stop")
async def stop(ctx):
    global song_queue, voice_client
    if voice_client:
        voice_client.stop()  # Stop the current song
        song_queue.clear()  # Clear the playlist queue
        await ctx.send("Jié mis une tempête mon gâté, j'ai tout viré, t'inquietes meme pas.")
        
        # Optionally, disconnect from the voice channel after stopping
        await voice_client.disconnect()
        await ctx.send("Bisous le S.")
    else:
        await ctx.send("Tié est fada toi? ya rien en cours mon frerot")

@bot.command(name='commands')
async def commands_help(ctx):
    help_message = """
    **Commandes possibles avec le cousin:**
    `!join` - Tu fais venir le couz dans le tchat
    `!leave` - Le couz en a marre donc il se barre
    `!play <url>` - Demandes au couz une musique Youtube, il a pas besoin d'etre deja sur le chat, il te rejoint tkt pas mon gâté
    `!stop` - Bah le couz il dégomme la sono
    `!pause` - On met sa douce main caleuse sur la platine
    `!resume` - Il enleve sa paluche de gorille de la platine
    `!next` - Le couz il tej le son qui est en train de jouer. Oui.
    """
    await ctx.send(help_message)

# Run the bot
bot.run(TOKEN)