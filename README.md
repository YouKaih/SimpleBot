# Simple Discord Music Bot

A straightforward Discord bot for playing music from YouTube and SoundCloud in your voice channels. It supports queuing songs, playlist links, and basic playback controls.

## Features

*   **Music Playback:** Play audio from YouTube and SoundCloud URLs.
*   **Playlist Support:** Add entire playlists from YouTube or SoundCloud to the queue.
*   **Song Queue:** Songs are added to a queue and play sequentially.
*   **Playback Controls:**
    *   `!play <URL or Playlist URL>`: Plays or adds to queue.
    *   `!pause`: Pauses the current song.
    *   `!resume`: Resumes a paused song.
    *   `!skip`: Skips to the next song in the queue.
    *   `!stop`: Stops playback and clears the queue.
*   **Information Commands:**
    *   `!nowplaying` (`!np`): Shows the currently playing song.
    *   `!queue` (`!q`): Displays the current song queue.
*   **Volume Control:** Adjust playback volume with `!volume <0-100>` (alias `!vol`). Volume is retained between songs.
*   **Help Command:** `!help` lists all available commands.
*   **Easy Setup:** Designed for relatively simple setup and use.

## Prerequisites

*   **Python 3.8+**
*   **FFmpeg:** Must be installed and accessible in your system's PATH.

## Setup and Commands

For detailed setup instructions, including how to create a Discord bot token, install dependencies, and configure the bot, please see:

➡️ **[INSTRUCTIONS.md](INSTRUCTIONS.md)**

The `INSTRUCTIONS.md` file also contains a full list of commands and their usage.

## Basic Usage Example

1.  Invite the bot to your server (see `INSTRUCTIONS.md`).
2.  Join a voice channel.
3.  Type `!join` for the bot to join your channel.
4.  Type `!play https://www.youtube.com/watch?v=your_video_id` to play a song.
5.  Type `!volume 70` to set the volume.

---

Enjoy the music!
