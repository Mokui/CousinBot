import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import yt_dlp
import asyncio
import logging
import tempfile

# Suppress discord.player error messages
discord_logger = logging.getLogger('discord.player')
#discord_logger.setLevel(logging.CRITICAL)  # Suppresses ERROR logs
print("=== Démarrage du bot ===")
load_dotenv()
TOKEN: str = os.getenv('DISCORD_TOKEN')

intents: discord.Intents = discord.Intents.default()
intents.message_content = True

# Set up the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Ensure FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -timeout 600',
    'options': '-vn -loglevel panic -prefer-ipv4',
    'executable': r'C:\Users\Mokui\Documents\ffmpeg-2025-01-02-git-0457aaf0d3-essentials_build\bin\ffmpeg.exe',
}

# YTDL options
YDL_OPTIONS = {
    'format': 'bestaudio/best', 
    'noplaylist': True,
    'retries': 3,
    'extract_flat': True,  # Don't download the full video, just extract info
    'geo_bypass': True,
    'source_address': '0.0.0.0',
    'extractaudio': True,  # Only extract audio,
    'default_search': 'auto',
    'quiet': False,
    'no_warnings':True,
    'ignoreerrors': True,
    'timeout': 600,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'webm',  # Or use 'opus' if preferred
        'preferredquality': '192',
    }],
}

# Update YDL_OPTIONS to accommodate playlist download specifics
playlist_YDL_OPTIONS = {
    'format': 'bestaudio/best',  # Best audio format
    'noplaylist': False,  # Allow playlist processing
    'retries': 3,
    'quiet': True,
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

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")


# Command to join a voice channel
@bot.command(name="join")
async def join(ctx):
    print(f"BOT JOINED")
    voice_channel = ctx.author.voice.channel if ctx.author.voice else None
    if not voice_channel:
        await ctx.send("T'es même pas dans un canal vocal, cousin.")
        return None

    # Si déjà connecté à un autre salon, on se déconnecte proprement
    if ctx.voice_client and ctx.voice_client.is_connected():
        if ctx.voice_client.channel == voice_channel:
            print("[LOG] Déjà connecté au channel")
            return ctx.voice_client
        else:
            # Si connecté ailleurs → on déconnecte
            await ctx.voice_client.disconnect(force=True)
            await asyncio.sleep(1)

    try:
        vc = await voice_channel.connect(reconnect=True, timeout=10)
        print(f"[LOG] Connecté au channel {voice_channel.name}")
        await ctx.send(f"J'suis dans ton vocal frère. Calmes toi mnt ")
        return vc

    except discord.ClientException as e:
        print(f"[ERROR] ClientException: {e}")
        await ctx.send("Y'a une galère mon copain. Attends un peu.")
        return None
    except Exception as e:
        print(f"[ERROR] Exception join: {e}")
        await ctx.send(f"Pas possible mon frérot : {e}")
        return None


# Command to leave a voice channel
@bot.command(name="leave")
async def leave(ctx):
    print(f"BOT LEAVED")
    if ctx.voice_client:
        await ctx.voice_client.disconnect(force=True)
        await ctx.send("Azy je trace, des poutous partout")
    else:
        await ctx.send("Jsuis meme pas là mon gâté!")

# Command to play audio from YouTube (stream HLS compatible)
@bot.command(name="play")
async def play(ctx, url: str):
    print(f"BOT ASKED TO PLAY")
    global voice_client

    voice_client = await ensure_voice(ctx)
    if not voice_client:
        return

    # Si une musique est en cours, on l’arrête
    if voice_client.is_playing():
        voice_client.stop()
        print("[LOG] Musique précédente arrêtée")

    try:
        # Options YTDL
        ydl_opts = YDL_OPTIONS.copy()
        ydl_opts.pop('extract_flat', None)
        ydl_opts['format'] = 'bestaudio/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Vérification restriction d'âge
            if info.get("age_limit", 0) >= 18:
                await ctx.send("Wesh ma gueule: ta vidéo a une restriction d'âge. J'suis pas majeur tavu")
                return

            audio_url = info.get("url")
            if not audio_url:
                await ctx.send("Impossible de lire cette vidéo")
                return
            
            # Juste avant de lancer → revérifie connexion
            if not voice_client.is_connected():
                voice_client = await ensure_voice(ctx)
                if not voice_client:
                    return

            # Lecture avec ffmpeg
            source = discord.FFmpegPCMAudio(
                audio_url,
                executable=FFMPEG_OPTIONS['executable'],
                before_options=FFMPEG_OPTIONS['before_options'],
                options="-vn -loglevel panic -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            )

            voice_client.play(source, after=lambda e: print(f"[LOG] Finito: {e}"))
            await ctx.send(f"Lecture de : **{info.get('title')}**")
            print(f"[LOG] Lecture de: {info.get('title')} - URL: {audio_url}")

    except Exception as e:
        await ctx.send(f"Erreur lors de la lecture : {str(e)}")
        print(f"[ERROR] Exception dans !play: {e}")

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

    # Si plus connecté (ex: déconnecté manuellement ou crash Discord), on vide tout
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        song_queue.clear()
        voice_client = None
        return

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

@bot.command(name="add")
async def add(ctx, url: str):
    global song_queue
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            song_queue.append(info["webpage_url"])
            await ctx.send(f"J'te l'ai mis sous le coude mon cousin: **{info['title']}**. Il passe après le son en cours 🔥")
    except Exception as e:
        await ctx.send(f"Azy y'a eu un bug : {str(e)}")


@bot.command(name='commands')
async def commands_help(ctx):
    help_message = """
    **Commandes possibles avec le cousin:**
    `!join` - Tu fais venir le couz dans le tchat
    `!leave` - Le couz en a marre donc il se barre
    `!play <url>` - Demandes au couz une musique Youtube, il a pas besoin d'etre deja sur le chat, il te rejoint tkt pas mon gâté
    `!playlist <url>` - Demandes au couz une playlist Youtube, il arrive avec sa platine il va te mettre bien. tié un tigre toi.
    `!add` - Le couz te met le prochain son sous le coude 
    `!stop` - Bah le couz il dégomme la sono
    `!pause` - On met sa douce main caleuse sur la platine
    `!resume` - Il enleve sa paluche de gorille de la platine
    `!next` - Le couz il tej le son qui est en train de jouer. Oui.
    `!cringe` - Le couz il cringe pour toi
    """
    await ctx.send(help_message)

# Command to ask the bot to cringe for you
@bot.command(name="cringe")
async def cringe(ctx):
    message_text = "T'es génant frérot. Stop en fait."
    gif_url = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExZnpuZWlnNGFob3RoMHFxaXhwOThkYWxyeTZzcmdtdTdvNGIwNXU5ZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/fPgUmix9paUZHN3aj0/giphy.gif"  # Replace with your desired GIF URL

    # Send message
    await ctx.send(message_text)

    # Send GIF as an embed
    embed = discord.Embed()
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)

async def ensure_voice(ctx):
    """Assure que le bot est bien connecté à un salon vocal."""
    if ctx.voice_client and ctx.voice_client.is_connected():
        return ctx.voice_client

    if not ctx.author.voice:
        await ctx.send("❌ Tu dois être dans un canal vocal.")
        return None

    try:
        vc = await ctx.author.voice.channel.connect(reconnect=False)
        print(f"[LOG] Connecté au channel {ctx.author.voice.channel.name}")
        return vc
    except Exception as e:
        print(f"[ERROR] Connexion vocale échouée: {e}")
        await ctx.send(f"❌ Impossible de rejoindre: {e}")
        return None

# Run the bot
bot.run(TOKEN)