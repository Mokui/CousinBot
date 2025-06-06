# Discord Music Bot: CousinBot

This project is a Discord bot built using the `discord.py` library. It allows users to join voice channels, play songs from YouTube, manage playlists, and control playback with commands.

## Features

- **Join Voice Channels**: The bot can join a user's voice channel on command.
- **Play Music**: Plays songs from YouTube URLs.
- **Playlists**: Handles playlists, queues songs, and plays them sequentially.
- **Playback Control**: Pause, resume, skip, and stop songs.
- **Custom Help Command**: Provides a list of available commands.

## Prerequisites

1. **Python**: Install Python 3.8 or higher.
2. **Discord Bot Token**: Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications).
3. **FFmpeg**: Download and install FFmpeg. Ensure the executable is accessible in your system's PATH or specify its location in the bot's configuration.
4. **Dependencies**: Install the required Python packages:

```bash
pip install -r [REQUIREMENTS]
```

### Required Packages
- `discord.py`
- `yt_dlp`
- `python-dotenv`

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Create a `.env` file in the root directory and add your bot token:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   ```

3. Configure the path to the FFmpeg executable in the bot's script:
   ```python
   FFMPEG_OPTIONS = {
       'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
       'options': '-vn',
       'executable': r'C:\path\to\ffmpeg.exe',
   }
   ```

4. Run the bot:
   ```bash
   $ .\venv\Scripts\activate 
   $ python main.py
   ```

## Commands

| Command      | Description                                     |
|--------------|-------------------------------------------------|
| `!join`      | Joins the user's current voice channel.         |
| `!leave`     | Disconnects the bot from the voice channel.     |
| `!play <url>`| Plays a song from a YouTube URL.                |
| `!playlist <url>` | Adds songs from a YouTube playlist to the queue. |
| `!pause`     | Pauses the currently playing song.              |
| `!resume`    | Resumes the paused song.                        |
| `!next`      | Skips to the next song in the queue.            |
| `!nextsong`      | Skips to the next song in the playlist queue.            |
| `!stop`      | Stops the current song and clears the queue.    |
| `!cringe`      | It's funny.                                   |
| `!help`      | Displays the custom help message.               |

## Contributing
Feel free to fork this repository, submit issues, or create pull requests. Contributions are welcome!

## Troubleshooting

- **FFmpeg Issues**: Ensure FFmpeg is correctly installed and accessible.
- **Bot Not Responding**: Verify the bot token in the `.env` file and ensure it is connected to your Discord server.
- **YouTube Playback Errors**: Update the `yt_dlp` package regularly to handle YouTube changes:
  ```bash
  pip install -U yt-dlp
  ```

---

### Enjoy the music mon copaing! 🎵
