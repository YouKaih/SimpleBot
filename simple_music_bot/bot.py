import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp
import asyncio
import collections # For deque

# Load environment variables from .env file
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not DISCORD_BOT_TOKEN:
    print("Error: DISCORD_BOT_TOKEN not found in environment variables or .env file.")
    exit()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content for commands
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None) # Remove default help command

song_queue = collections.deque() # Initialize the song queue
current_bot_volume = 0.5 # Default volume at 50%

# Options for initial info extraction (can handle playlists)
YDL_OPTS_INFO = {
    'format': 'bestaudio/best',
    'noplaylist': False,        # Allow processing of playlists
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,       # Get a flat list of playlist entries (URLs or IDs)
                                # This is simpler for queueing page URLs.
    'lazy_playlist': True,
    # 'dump_single_json': True, # Alternative: get full JSON for parsing if needed
    'source_address': '0.0.0.0',
}

# Options for fetching the actual stream URL before playback
YDL_OPTS_PLAYBACK = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',  # No video
}

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} is ready!')
    print(f'Connected to {len(bot.guilds)} guilds.')
    await bot.change_presence(activity=discord.Game(name="music | !play <URL>"))

# --- Queue and Playback Logic ---
async def play_next_in_queue_after_event_wrapper(ctx: commands.Context, error=None):
    """Wrapper for the 'after' callback to correctly schedule play_next_in_queue."""
    if error:
        print(f"Player error: {error}")
        # Optionally send a message to the channel, but be mindful of spam if errors are frequent
        # await ctx.send(f"Playback error: {error}. Trying next song...")

    # This function is called by the `after` lambda, which uses `run_coroutine_threadsafe`.
    # It's already running within the bot's event loop context here.
    await play_next_in_queue(ctx)


async def play_next_in_queue(ctx: commands.Context):
    """Plays the next song from the global song_queue."""
    global song_queue
    if not song_queue:
        # await ctx.send("Queue finished.") # Optional message
        return

    if not ctx.voice_client or not ctx.voice_client.is_connected():
        # await ctx.send("Bot is not connected to a voice channel to play the next song.") # Optional
        return

    # Stop current playback if any (e.g., if skip was called, it stops, then this plays next)
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        ctx.voice_client.stop()
        await asyncio.sleep(0.5) # Brief pause for stop to take effect

    song_data = song_queue.popleft()
    url_to_play = song_data.get('url') # This should be the page URL / ID

    async with ctx.typing():
        try:
            # Get fresh stream info for this specific track URL/ID
            with yt_dlp.YoutubeDL(YDL_OPTS_PLAYBACK) as ydl:
                playback_info = ydl.extract_info(url_to_play, download=False)

            stream_url = None
            if 'url' in playback_info and playback_info['url'].startswith(('http://', 'https://')):
                 stream_url = playback_info['url']
            if not stream_url: # Fallback to formats
                formats = playback_info.get('formats', [])
                for f in sorted(formats, key=lambda x: x.get('abr', 0) or x.get('tbr', 0), reverse=True):
                    if f.get('url') and (f.get('acodec') != 'none' and f.get('acodec') is not None):
                        stream_url = f.get('url')
                        break

            if not stream_url:
                await ctx.send(f"Could not get a streamable URL for '{song_data.get('title', url_to_play)}'. Skipping.")
                await play_next_in_queue(ctx) # Try next song
                return

            ffmpeg_source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
            # Use the stored global volume
            global current_bot_volume
            volume_source = discord.PCMVolumeTransformer(ffmpeg_source, volume=current_bot_volume)

            # Attach metadata for !nowplaying
            volume_source.title = song_data.get('title', playback_info.get('title', 'Unknown Title'))
            volume_source.uploader = song_data.get('uploader', playback_info.get('uploader', playback_info.get('channel', 'Unknown Artist')))

            # Correctly schedule the after event
            ctx.voice_client.play(volume_source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_in_queue_after_event_wrapper(ctx, e), bot.loop))
            await ctx.send(f"**Now playing:** {volume_source.title} by {volume_source.uploader}")

        except yt_dlp.utils.DownloadError as e:
            await ctx.send(f"Error processing `{song_data.get('title', url_to_play)}`: {e}. Skipping.")
            await play_next_in_queue(ctx) # Try next song
        except Exception as e:
            await ctx.send(f"Unexpected error playing `{song_data.get('title', url_to_play)}`: {e}. Skipping.")
            print(f"Error in play_next_in_queue for '{url_to_play}': {type(e).__name__} - {e}")
            await play_next_in_queue(ctx) # Try next song

async def ensure_voice_channel(ctx: commands.Context):
    """Checks if user is in a voice channel, if bot is, and connects/moves if necessary."""
    if not ctx.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return None

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        try:
            vc = await voice_channel.connect(timeout=5.0) # Add timeout
            return vc
        except asyncio.TimeoutError:
            await ctx.send(f"Timed out trying to connect to `{voice_channel.name}`.")
            return None
        except Exception as e:
            await ctx.send(f"Error connecting to voice channel: {e}")
            return None

    elif ctx.voice_client.channel != voice_channel:
        try:
            await ctx.voice_client.move_to(voice_channel)
        except Exception as e:
            await ctx.send(f"Error moving to voice channel: {e}")
            return None # Failed to move

    return ctx.voice_client # Return current client if already in correct channel or successfully moved

@bot.command(name='join', help='Tells the bot to join your current voice channel.')
async def join(ctx: commands.Context):
    vc = await ensure_voice_channel(ctx)
    if vc:
        await ctx.send(f"Joined `{vc.channel.name}`.")

@bot.command(name='leave', help='To make the bot leave the voice channel.')
async def leave(ctx: commands.Context):
    global song_queue
    if ctx.voice_client:
        channel_name = ctx.voice_client.channel.name
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        song_queue.clear() # Clear queue on leave
        await ctx.voice_client.disconnect()
        await ctx.send(f"Left `{channel_name}` and cleared queue.")
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command(name='play', help='Plays a song or adds a playlist to the queue from a YouTube/SoundCloud URL.')
async def play(ctx: commands.Context, *, query_url: str):
    global song_queue
    voice_client = await ensure_voice_channel(ctx)
    if not voice_client:
        return

    async with ctx.typing():
        try:
            # Use YDL_OPTS_INFO for initial extraction, might be a playlist
            with yt_dlp.YoutubeDL(YDL_OPTS_INFO) as ydl:
                info = ydl.extract_info(query_url, download=False)

            added_to_queue_count = 0
            if '_type' in info and info['_type'] == 'playlist':
                # It's a playlist, info['entries'] contains flat list of URLs due to 'extract_flat': True
                for entry in info.get('entries', []):
                    if entry and entry.get('url'): # yt-dlp with extract_flat gives basic entries
                        # For playlists, we often get just the URL. Title/uploader might be missing here.
                        # We'll try to get them when play_next_in_queue processes each one.
                        song_data = {
                            'url': entry.get('webpage_url', entry.get('url')), # Prefer webpage_url if available
                            'title': entry.get('title', 'Unknown Title from Playlist'), # Placeholder
                            'uploader': entry.get('uploader', 'Unknown Artist') # Placeholder
                        }
                        song_queue.append(song_data)
                        added_to_queue_count += 1
                if added_to_queue_count > 0:
                    await ctx.send(f"Added {added_to_queue_count} songs from the playlist to the queue.")
                else:
                    await ctx.send("Found a playlist, but could not add any songs from it.")
            else:
                # Single video (or yt-dlp couldn't identify as playlist with entries)
                # We need its page URL, title, and uploader for the queue.
                # The initial `info` from YDL_OPTS_INFO might be enough if not extract_flat,
                # or we might need a slightly different YDL_OPTS for single track details if extract_flat is too basic.
                # For now, assume `info` for a single track has what we need.
                # If `extract_flat: True` was used, `info` would be the entry itself.

                # Let's re-fetch with different opts if `extract_flat` made it too basic for a single song
                # This is a bit inefficient but ensures we get title/uploader for single songs too.
                # A better way would be to have yt-dlp return full info for single items even with extract_flat,
                # or parse more carefully.
                if 'entries' not in info: # Likely a single video
                     with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}) as ydl_single:
                         single_info = ydl_single.extract_info(query_url, download=False)
                         song_data = {
                             'url': single_info.get('webpage_url', query_url),
                             'title': single_info.get('title', 'Unknown Title'),
                             'uploader': single_info.get('uploader', single_info.get('channel', 'Unknown Artist'))
                         }
                         song_queue.append(song_data)
                         await ctx.send(f"Added to queue: **{song_data['title']}** by {song_data['uploader']}")
                         added_to_queue_count = 1
                else: # Should not happen if _type was not playlist and extract_flat=True
                    await ctx.send("Could not process the provided link as a single song or playlist.")
                    return


            if added_to_queue_count > 0 and not voice_client.is_playing() and not voice_client.is_paused():
                await play_next_in_queue(ctx)

        except yt_dlp.utils.DownloadError as e:
            await ctx.send(f"Error processing URL: {e}")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
            print(f"Error in play command for '{query_url}': {type(e).__name__} - {e}")

@bot.command(name='stop', help='Stops playback and clears the song queue.')
async def stop(ctx: commands.Context):
    global song_queue
    song_queue.clear()
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        ctx.voice_client.stop()
        await ctx.send("Playback stopped and queue cleared.")
    else:
        await ctx.send("Not playing anything, but queue cleared.") # Or just "Queue cleared."

@bot.command(name='pause', help='Pauses the current audio playback.')
async def pause(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Playback paused.")
    elif ctx.voice_client and ctx.voice_client.is_paused():
        await ctx.send("Playback is already paused.")
    else:
        await ctx.send("Not playing anything to pause.")

@bot.command(name='resume', help='Resumes paused audio playback.')
async def resume(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Playback resumed.")
    elif ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.send("Playback is already ongoing.")
    else:
        await ctx.send("Nothing to resume.")

@bot.command(name='queue', aliases=['q'], help='Displays the current song queue.')
async def show_queue(ctx: commands.Context):
    global song_queue
    embed = discord.Embed(title="Music Queue", color=discord.Color.purple())

    if ctx.voice_client and ctx.voice_client.source:
        current_source = ctx.voice_client.source
        title = getattr(current_source, 'title', 'Currently Playing Track')
        uploader = getattr(current_source, 'uploader', '')
        embed.add_field(name="Now Playing", value=f"**{title}**\nby {uploader if uploader else 'Unknown Artist'}", inline=False)
    else:
        embed.add_field(name="Now Playing", value="Nothing currently playing.", inline=False)

    if not song_queue:
        embed.add_field(name="Up Next", value="The queue is empty!", inline=False)
    else:
        queue_list_str = ""
        for i, song_data in enumerate(song_queue):
            title = song_data.get('title', 'Unknown Title')
            # uploader = song_data.get('uploader', 'Unknown Artist') # Could add uploader too
            queue_list_str += f"{i+1}. {title}\n"
            if i >= 9: # Limit display to 10 upcoming songs for brevity
                queue_list_str += f"...and {len(song_queue) - (i+1)} more."
                break
        embed.add_field(name=f"Up Next ({len(song_queue)} songs)", value=queue_list_str if queue_list_str else "Empty", inline=False)

    await ctx.send(embed=embed)

@bot.command(name='skip', help='Skips the current song and plays the next in queue.')
async def skip(ctx: commands.Context):
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        await ctx.send("Skipping current song...")
        ctx.voice_client.stop() # This will trigger the 'after' callback (play_next_in_queue_after_event_wrapper)
                               # which then calls play_next_in_queue.
    else:
        await ctx.send("Not playing anything to skip.")

@bot.command(name='nowplaying', aliases=['np'], help='Shows the currently playing song.')
async def nowplaying(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.source:
        source = ctx.voice_client.source
        if hasattr(source, 'title') and hasattr(source, 'uploader'):
            title = source.title
            uploader = source.uploader
            embed = discord.Embed(
                title="Now Playing",
                description=f"**{title}**\nby {uploader}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("Currently playing a song, but its details are unavailable.")
    else:
        await ctx.send("Not playing anything at the moment.")

@bot.command(name='volume', aliases=['vol'], help='Changes the player\'s volume (0-100).')
async def volume(ctx: commands.Context, level: int = None):
    if not ctx.voice_client or not ctx.voice_client.source:
        return await ctx.send("Not playing anything right now.")

    if level is None:
        if isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
            current_volume = int(ctx.voice_client.source.volume * 100)
            return await ctx.send(f"Current volume is: {current_volume}%")
        else:
            return await ctx.send("Current volume is unknown (audio source not standard for volume control).")

    if not (0 <= level <= 100):
        return await ctx.send("Volume must be between 0 and 100.")

    # discord.py's default FFmpegPCMAudio source is not a PCMVolumeTransformer initially.
    # It gets wrapped when VoiceClient.play is called, or if you manually wrap it.
    # To adjust volume, the source *must* be a PCMVolumeTransformer.
    # If it's already playing, it should be wrapped.
    if isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
        global current_bot_volume
        new_volume_float = level / 100
        ctx.voice_client.source.volume = new_volume_float
        current_bot_volume = new_volume_float # Update global state
        await ctx.send(f"Volume set to {level}%.")
    else:
        # This case should ideally not be hit if music is playing because play() wraps it.
        # If it is, it means something is unusual, or the source was replaced.
        await ctx.send("Cannot adjust volume for the current audio type. This is unexpected.")
        print(f"Volume command: voice_client.source is not PCMVolumeTransformer. Type: {type(ctx.voice_client.source)}")

@bot.command(name='help', help='Shows this help message.')
async def custom_help(ctx: commands.Context):
    embed = discord.Embed(
        title="Bot Commands",
        description="Here's a list of available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(name="`!join`", value="Bot joins your current voice channel.", inline=False)
    embed.add_field(name="`!leave`", value="Bot leaves, stopping music and clearing the queue.", inline=False)
    embed.add_field(name="`!play <URL or Playlist URL>`", value="Plays a song or adds a YouTube/SoundCloud playlist to the queue.\nExample: `!play https://www.youtube.com/playlist?list=PLyourlistID`", inline=False)
    embed.add_field(name="`!pause`", value="Pauses the current audio playback.", inline=False)
    embed.add_field(name="`!resume`", value="Resumes paused audio playback.", inline=False)
    embed.add_field(name="`!skip`", value="Skips the current song and plays the next in queue.", inline=False)
    embed.add_field(name="`!stop`", value="Stops playback and clears the entire queue.", inline=False)
    embed.add_field(name="`!nowplaying` (`!np`)", value="Shows the currently playing song.", inline=False)
    embed.add_field(name="`!queue` (`!q`)", value="Displays the current song queue.", inline=False)
    embed.add_field(name="`!volume <0-100>` (`!vol`)", value="Sets playback volume (e.g., `!volume 50`). Shows current volume if no number is given.", inline=False)
    embed.add_field(name="`!help`", value="Shows this help message.", inline=False)

    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
    else:
        # This was already checked at the start, but as a safeguard.
        print("CRITICAL: DISCORD_BOT_TOKEN is not defined. Bot cannot start.")
