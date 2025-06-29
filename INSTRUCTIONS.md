# Simple Discord Music Bot Setup

This guide will help you set up and run this simple Discord Music Bot.

**Features:**
*   Plays audio from YouTube and SoundCloud URLs.
*   Volume control.
*   Simple commands.

## 1. Prerequisites

### a. Discord Bot Token
1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Click **"New Application"**. Give it a name (e.g., "SimpleMusicBot") and click "Create".
3.  Go to the **"Bot"** tab on the left.
4.  Click **"Add Bot"** and confirm ("Yes, do it!").
5.  Under the "Privileged Gateway Intents" section, enable:
    *   **Message Content Intent** (Required for reading commands like `!play <url>`).
6.  Click **"Reset Token"** (or "View Token"/"Copy Token"). Copy this token. **Treat it like a password and keep it secret!** You'll need this for the `.env` file later.

### b. Python
*   Ensure Python 3.8 or newer is installed. You can download it from [python.org](https://www.python.org/downloads/).
*   During installation on Windows, make sure to check the box that says **"Add Python to PATH"**.

### c. FFmpeg
FFmpeg is required for processing audio.
*   **Windows:**
    1.  Download a static build from a reputable source like [Gyan.dev FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/) (e.g., `ffmpeg-release-full.7z`).
    2.  Extract the archive (e.g., using 7-Zip) to a location like `C:\ffmpeg`.
    3.  Add the `bin` directory from the extracted folder (e.g., `C:\ffmpeg\bin`) to your system's PATH environment variable.
        *   Search for "environment variables" in Windows search.
        *   Click "Edit the system environment variables".
        *   Click "Environment Variables...".
        *   Under "System variables", find "Path", select it, click "Edit...", then "New", and paste the path to FFmpeg's `bin` folder.
        *   Click "OK" on all dialogs. Restart your terminal or VS Code (or even your PC) for changes to take effect.
*   **macOS:**
    ```bash
    brew install ffmpeg
    ```
*   **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt update && sudo apt install -y ffmpeg
    ```

## 2. Bot Setup

### a. Download or Clone the Code
*   If you have the code as a ZIP, download and extract it. The `simple_music_bot` folder and this `INSTRUCTIONS.md` should be in the root of your project.
*   Or, clone it using Git: `git clone <repository_url>`

### b. Navigate to the Bot Script Directory
Open your terminal or command prompt. Navigate into the `simple_music_bot` directory where `bot.py` is located.
```bash
cd path/to/your/project_folder/simple_music_bot
```

### c. Set up Virtual Environment & Install Dependencies
It's highly recommended to use a virtual environment within the `simple_music_bot` directory.
```bash
# Ensure you are inside the simple_music_bot directory
python -m venv venv
```
Activate the virtual environment:
*   Windows: `.\venv\Scripts\activate`
*   macOS/Linux: `source ./venv/bin/activate`

Once activated (you should see `(venv)` in your terminal prompt), install the required Python packages. A `requirements.txt` file will be provided.
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` is not yet available or you're doing a manual setup, the command would be: `pip install discord.py yt-dlp PyNaCl python-dotenv`)*

### d. Configure Bot Token
1.  Inside the `simple_music_bot` directory (where `bot.py` is), you'll find a file named `.env.example`.
2.  Create a copy of this file in the **same directory** and rename the copy to `.env`.
3.  Open the `.env` file with a text editor.
4.  You will see the line: `DISCORD_BOT_TOKEN="YOUR_TOKEN_HERE"`
5.  Replace `"YOUR_TOKEN_HERE"` with the actual Discord Bot Token you copied in Step 1a.
    ```env
    DISCORD_BOT_TOKEN="AbCdEfGhIjKlMnOpQrStUvWxYz.123456.abcdefghijklmnopqrs" # Example token
    ```
6.  Save the `.env` file. This file is listed in `.gitignore` at the project root, so your token won't be accidentally committed if you're using Git.

## 3. Running the Bot

1.  Ensure your virtual environment is still active within the `simple_music_bot` directory. If not, navigate to `simple_music_bot` and activate it (`.\venv\Scripts\activate` or `source ./venv/bin/activate`).
2.  Run the bot script:
    ```bash
    python bot.py
    ```
3.  If everything is set up correctly, you'll see a message in the console like `Bot YourBotName is ready!`.

## 4. Inviting the Bot to Your Server

1.  Go back to your bot's application page on the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Go to the **"OAuth2"** tab, then **"URL Generator"**.
3.  Under **"Scopes"**, select `bot`.
4.  Under **"Bot Permissions"**, select at least:
    *   `Send Messages` (or `Send Messages in Threads`)
    *   `Read Message History` (sometimes useful for context)
    *   `Connect` (to join voice channels)
    *   `Speak` (to play audio)
    *   `Use Voice Activity` (usually default, good to have)
5.  Copy the generated "INVITE URL" at the bottom.
6.  Paste this URL into your web browser, select the server you want to add the bot to, and click "Authorize".

## 5. Bot Commands

*   `!join`: The bot will join the voice channel you are currently in.
*   `!leave`: The bot will leave its current voice channel, stop playing, and clear the queue.
*   `!play <YouTube/SoundCloud URL or Playlist URL>`: Plays a song or adds songs from a playlist to the queue. If already playing, songs are added to the end of the queue.
    *   Example (single song): `!play https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    *   Example (playlist): `!play https://www.youtube.com/playlist?list=PLyourPlaylistID`
*   `!pause`: Pauses the current audio playback.
*   `!resume`: Resumes paused audio playback.
*   `!skip`: Skips the current song and plays the next one in the queue (if any).
*   `!stop`: Stops the currently playing audio and clears the entire queue.
*   `!nowplaying` (or `!np`): Shows details about the currently playing song.
*   `!queue` (or `!q`): Displays the current song queue, including the playing song and upcoming tracks.
*   `!volume <0-100>` (or `!vol <0-100>`): Sets the playback volume (e.g., `!volume 50`). If no number is given, it shows the current volume.
*   `!help`: Shows a list of all available commands.

Enjoy your music bot!
