import discord
from dotenv import load_dotenv
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import asyncio
import random
import re
import os
import json

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="b!", intents=intents)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

if token is None:
    print("Token is None. Check your .env file.")
else:
    print("Token loaded successfully.")

# --- yt-dlp OPTIONS ---
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

# --- MUSIC PLAYERS DICT ---
music_players = {}

def get_music_player(ctx):
    guild_id = ctx.guild.id
    if guild_id not in music_players:
      music_players[guild_id] = MusicPlayer(ctx)
    return music_players[guild_id]

# Music Player Class
class MusicPlayer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.voice_client = None
        self.queue = []
        self.is_playing = False
        self.current = None
        self.loop = False

    async def connect_to_voice(self):
        if self.voice_client and self.voice_client.is_connected():
            return True  # Already connected
        if self.ctx.author.voice is None:
            await self.ctx.send("You must be in a voice channel to use this command.")
            return False

        channel = self.ctx.author.voice.channel
        try:
            self.voice_client = await channel.connect()
            return True
        except Exception as e:
            print(f"Error connecting to voice channel: {e}")
            await self.ctx.send("I could not join your voice channel.")
            return False

    async def play_next(self):
      if not self.voice_client or not self.voice_client.is_connected():
          self.is_playing = False
          return

      if self.queue:
          song = self.queue.pop(0)  # Get the next song from the queue
          self.current = song
          try:
            self.is_playing = True
            self.voice_client.play(discord.FFmpegPCMAudio(song['url']), after=lambda e: asyncio.run_coroutine_threadsafe(self.after_song(e), bot.loop))
          except Exception as e:
            print(f"Error playing song: {e}")
            self.is_playing = False
            await self.ctx.send(f"Error playing: {song['title']}")
            return
      else:
          self.is_playing = False
          self.current = None
          if self.loop and self.current:
             self.queue.append(self.current)
             await self.play_next()
          elif self.voice_client:
            self.voice_client.pause()
            
    async def after_song(self, error):
        if error:
            print(f"Error in after_song: {error}")
        await self.play_next()

    def clear_queue(self):
        self.queue.clear()

    def queue_count(self):
        return len(self.queue)
    
    def toggle_loop(self):
         self.loop = not self.loop

# --- EVENT: BOT READY ---
@bot.event
async def on_ready():
    print("The Bumbling Bard is ready to sing!")

# Spotify API setup
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    print("Spotify API keys loaded successfully.")
else:
    sp = None
    print("Spotify API keys not found. Spotify functionality will be disabled.")



# --- COMMAND: SING ---
@bot.command(name="sing")
async def sing(ctx, *, url: str = None):
    if url is None:
      await ctx.send("The bard needs a song to sing! 🎶")
      return
    player = get_music_player(ctx)
    if not player:
        await ctx.send("The bard is missing a player to sing with. 🎶")
        return
    if not await player.connect_to_voice():
        return
    try:
        await handle_video(ctx, url, player)
    except Exception as e:
        await ctx.send(f"The bard encountered an error: {str(e)}")
        print(f"Error in sing: {e}")


async def handle_video(ctx, url, player):
    loop = asyncio.get_event_loop()
    MAX_PLAYLIST_SIZE = 50

    async def process_info(info):
        if not isinstance(info, dict):
            await ctx.send("The bard could not decipher this tale. 🎶")
            return

        if info.get('_type') == 'playlist':
            entries = info.get('entries', [])
            total_entries = len(entries)

            if total_entries > MAX_PLAYLIST_SIZE:
                await ctx.send(f"⚠️ This playlist is too large to process. Maximum allowed size is {MAX_PLAYLIST_SIZE} entries.")
                return

            await ctx.send(f"🎶 Adding {total_entries} songs from playlist...")

            # Collect all video info first. This makes it so that the entire playlist is processed before starting any playback
            video_infos = []
            for entry in entries:
              if not entry or not entry.get('id'):
                continue
              try:
                  video_info = await loop.run_in_executor(
                      None,
                      lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(
                          f"https://www.youtube.com/watch?v={entry['id']}",
                          download=False
                      )
                  )
                  video_infos.append(video_info)
              except Exception as e:
                  print(f"Error processing playlist entry {entry.get('id')}: {e}")
                  continue

            for video_info in video_infos:
              formats = video_info.get('formats', [])
              audio_formats = [f for f in formats if f.get('acodec') != 'none']
              if audio_formats:
                  best_audio = audio_formats[-1]
                  player.queue.append({
                      'url': best_audio['url'],
                      'title': video_info['title']
                  })
            await ctx.send("✅ Playlist has been added to the repertoire!")
        else:
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('acodec') != 'none']
            if audio_formats:
              best_audio = audio_formats[-1]
              player.queue.append({
                    'url': best_audio['url'],
                    'title': info['title']
                })
              await ctx.send(f"🎶 Added to repertoire: **{info['title']}**")

    
    # Check if spotify url
    if "spotify.com" in url:
        if sp is None:
            await ctx.send("The bard cannot access Spotify right now. Please try again later.")
            return

        if "playlist" in url:
            await handle_spotify_playlist(ctx, url, player)
        elif "track" in url:
           await handle_spotify_track(ctx, url, player)
        else:
            await ctx.send("The bard can only read Spotify playlists or tracks! 🎶")
        return

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      try:
        info = await loop.run_in_executor(None, ydl.extract_info, url, False)
        await process_info(info)
      except Exception as e:
        await ctx.send("The bard encountered a problem fetching this tale. 🎶")
        print(f"Error in handle_video: {e}")
        return

    if not player.is_playing and player.queue:
      await player.play_next()


async def handle_spotify_playlist(ctx, url, player):
    loop = asyncio.get_event_loop()
    MAX_PLAYLIST_SIZE = 50

    try:
        playlist_id = url.split("/")[-1].split("?")[0]
        playlist = sp.playlist(playlist_id)
        total_tracks = playlist['tracks']['total']

        if total_tracks > MAX_PLAYLIST_SIZE:
            await ctx.send(f"⚠️ This playlist is too large to process. Maximum allowed size is {MAX_PLAYLIST_SIZE} tracks.")
            return

        await ctx.send(f"🎶 Adding {total_tracks} tracks from Spotify playlist...")

        track_items = playlist['tracks']['items']
        
        track_titles = []
        for item in track_items:
            track = item['track']
            if track is None:
              continue # Skip local files
            track_name = track['name']
            artists = ", ".join([artist['name'] for artist in track['artists']])
            query = f"{track_name} by {artists}"
            track_titles.append(query)

        # Fetch youtube video urls for each track
        video_infos = []
        for track_query in track_titles:
          try:
            video_info = await loop.run_in_executor(
                      None,
                      lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(
                          f"ytsearch:{track_query}",
                          download=False
                      )
            )
            if video_info and video_info['entries']:
                video_infos.append(video_info['entries'][0])
          except Exception as e:
              print(f"Error processing track query {track_query}: {e}")
              continue


        for video_info in video_infos:
          formats = video_info.get('formats', [])
          audio_formats = [f for f in formats if f.get('acodec') != 'none']
          if audio_formats:
            best_audio = audio_formats[-1]
            player.queue.append({
                'url': best_audio['url'],
                'title': video_info['title']
              })
        await ctx.send("✅ Spotify playlist has been added to the repertoire!")
    
    except Exception as e:
        print(f"Error handling spotify playlist: {e}")
        await ctx.send("The bard encountered a problem fetching this playlist from spotify. 🎶")


async def handle_spotify_track(ctx, url, player):
    loop = asyncio.get_event_loop()
    try:
        track_id = url.split("/")[-1].split("?")[0]
        track = sp.track(track_id)
        track_name = track['name']
        artists = ", ".join([artist['name'] for artist in track['artists']])
        query = f"{track_name} by {artists}"

        video_info = await loop.run_in_executor(
              None,
              lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(
                  f"ytsearch:{query}",
                  download=False
              )
        )
        if video_info and video_info['entries']:
          video_info = video_info['entries'][0]
          formats = video_info.get('formats', [])
          audio_formats = [f for f in formats if f.get('acodec') != 'none']
          if audio_formats:
            best_audio = audio_formats[-1]
            player.queue.append({
              'url': best_audio['url'],
              'title': video_info['title']
            })
            await ctx.send(f"🎶 Added to repertoire: **{track_name}**")
        else:
            await ctx.send("Could not find a matching song on YouTube. 🎶")

    except Exception as e:
        print(f"Error handling spotify track: {e}")
        await ctx.send("The bard encountered a problem fetching this track from spotify. 🎶")



# --- COMMANDS ---
@bot.command(name="skip")
async def skip(ctx):
    player = get_music_player(ctx)
    if player.voice_client and player.voice_client.is_playing():
        player.voice_client.pause()
        await player.play_next()
        await ctx.send("The bard skips to the next tale. ⏭️")
    else:
      await ctx.send("The bard isn't singing anything to skip.")

@bot.command(name="pause")
async def pause(ctx):
    player = get_music_player(ctx)
    if player.voice_client and player.voice_client.is_playing():
        player.voice_client.pause()
        await ctx.send("The bard takes a breath. ⏸️")
    else:
      await ctx.send("The bard isn't singing anything right now.")

@bot.command(name="resume")
async def resume(ctx):
    player = get_music_player(ctx)
    if player.voice_client and player.voice_client.is_paused():
        player.voice_client.resume()
        await ctx.send("The bard resumes their tale! ▶️")
    else:
        await ctx.send("The bard wasn't paused.")

@bot.command(name="stop")
async def stop(ctx):
    player = get_music_player(ctx)
    if player.voice_client and (player.voice_client.is_playing() or player.voice_client.is_paused()):
        player.voice_client.pause()
        await ctx.send("The bard takes a breath and pauses the tale. ⏸️")
    else:
        await ctx.send("The bard isn't singing anything.")

@bot.command(name="leave")
async def leave(ctx):
    player = get_music_player(ctx)
    if player.voice_client is not None:
      await player.voice_client.disconnect()
      player.voice_client = None
      await ctx.send("The bard leaves the tavern. 👋")
    else:
        await ctx.send("The bard isn't in any tavern (voice channel).")

@bot.command(name="repertoire")
async def repertoire(ctx):
    player = get_music_player(ctx)
    if player.queue:
        songs = "\n".join([f"**{i + 1}. {song['title']}**" for i, song in enumerate(player.queue)])
        await ctx.send(f"🎶 The bard's repertoire:\n{songs}")
    else:
        await ctx.send("The bard's repertoire is empty! 🎶")


# --- OTHER COMMANDS ---
@bot.command(name="shuffle")
async def shuffle(ctx):
    player = get_music_player(ctx)
    if player.queue:
      random.shuffle(player.queue)
      await ctx.send("The bard shuffles their repertoire. 🔀")
    else:
      await ctx.send("The bard's repertoire is empty! 🎶")

@bot.command(name="loop")
async def loop(ctx):
    player = get_music_player(ctx)
    if player.is_playing or player.queue:
      player.toggle_loop()
      if player.loop:
          await ctx.send("The Bard will repeat the repertoire! 🔂")
      else:
          await ctx.send("The Bard is done with repeats! ⏯️")
    else:
      await ctx.send("The bard must be singing to enable looping. 🎶")

@bot.command(name="now")
async def now(ctx):
    player = get_music_player(ctx)
    if player.current:
        # Send the title of the currently playing video
        loop_status = "🔄 (Looping)" if player.loop else ""
        await ctx.send(f"🎶 Now playing: **{player.current['title']}** {loop_status}")
    else:
        await ctx.send("The bard isn't singing anything right now.")

@bot.command(name="next")
async def next(ctx):
    player = get_music_player(ctx)
    if player.queue:
        # Check for the next song in the queue
        next_song = player.queue[0]  # The next song is the first in the queue
        await ctx.send(f"🎶 Next in line: **{next_song['title']}**")
    else:
        await ctx.send("The bard's repertoire is empty! 🎶")

rarity_colors = {
    "common": discord.Color.light_grey(),  # Grey
    "uncommon": discord.Color.green(),    # Green
    "rare": discord.Color.blue(),        # Blue
    "epic": discord.Color.purple(),     # Purple (a good fit for Epic)
    "legendary": discord.Color.orange(),   # Orange
}

@bot.command(name="loot")
async def loot(ctx):
    """Generates a random loot item based on rarity."""
    try:
        with open('loot.json', 'r') as json_file:
            data = json.load(json_file)

        if not isinstance(data, dict) or 'loot' not in data:
            raise ValueError("Invalid loot.json format: Missing 'loot' key.")

        loot_data = data['loot']
        if not isinstance(loot_data, dict):
                raise ValueError("Invalid loot.json format: 'loot' is not a JSON object.")

        categories = []
        for rarity, details in loot_data.items():
           if "chance" not in details or "items" not in details:
               raise ValueError(f"Invalid loot.json format: missing chance or items in {rarity} category")
           categories.append((rarity, details['chance']))
           
        # Select a random rarity based on weighted chances
        rarities = [item[0] for item in categories]
        weights = [item[1] for item in categories]
        random_rarity = random.choices(rarities, weights=weights, k=1)[0]


        items_list = loot_data[random_rarity]['items']
        random_item = random.choice(items_list)
        
        item_rarity = random_item["rarity"].lower()
        
        # Determine the color based on rarity
        embed_color = rarity_colors.get(item_rarity, discord.Color.default()) # Default if not found
        
         # Create and send embed
        embed = discord.Embed(title=f"Loot Obtained", color=embed_color)
        embed.add_field(name="Item:", value=random_item["title"], inline=False)
        embed.add_field(name="Description:", value=random_item["description"], inline=False)
        embed.add_field(name="Rarity:", value=item_rarity.capitalize(), inline=False)
        embed.add_field(name="Chance:", value=f"{loot_data[random_rarity]['chance']}%", inline=False)
        await ctx.send(embed=embed)

    except FileNotFoundError:
        await ctx.send("Error: loot.json not found.")
    except json.JSONDecodeError:
        await ctx.send("Error: loot.json is not valid JSON.")
    except ValueError as e:
        await ctx.send(f"Error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

@bot.command(name="npc")
async def name(ctx):
    """Selects a random name from names.json with additional attributes."""
    try:
        with open('names.json', 'r') as json_file:
            data = json.load(json_file)

        # Validate JSON (same as before)
        if not isinstance(data, dict):
            raise ValueError("Invalid names.json format: Not a JSON object.")
        if 'names' not in data:
            raise ValueError("Invalid names.json format: Missing 'names' key.")
        if not isinstance(data['names'], list):
            raise ValueError("Invalid names.json format: 'names' is not an array.")
        if not data['names']:
            raise ValueError("The 'names' array in names.json is empty.")

        random_name = random.choice(data['names'])

        # Expanded attributes
        ages = ["Young Child", "Child", "Teenager", "Young Adult", "Adult", "Middle-Aged", "Older Adult", "Elderly"]
        personalities = [
    "Kind", "Brave", "Funny", "Wise", "Mysterious", "Mischievous", "Grumpy", 
    "Cheerful", "Quiet", "Loud", "Shy", "Extroverted", "Introverted", 
    "Ambitious", "Lazy", "Creative", "Logical", "Emotional", "Stoic", 
    "Curious", "Cautious", "Optimistic", "Pessimistic", "Honest", "Deceptive", 
    "Generous", "Selfish", "Compassionate", "Ruthless", "Adventurous", 
    "Romantic", "Skeptical", "Realistic", "Enthusiastic", "Pragmatic", 
    "Sentimental", "Imaginative", "Detail-oriented", "Laid-back", "Ambiguous", 
    "Playful", "Inquisitive", "Diligent", "Humble", "Assertive", "Witty", 
    "Rebellious", "Supportive", "Zany", "Introspective", "Charismatic", 
    "Idealistic", "Traditional", "Eclectic", "Sincere", "Patient", 
    "Impulsive", "Nurturing", "Analytical", "Independent", "Self-aware"
    ]

        random_age = random.choice(ages)
        random_personality = random.choice(personalities)

        # Create and send embed
        embed = discord.Embed(title=f"Random Character", color=discord.Color.blue())
        embed.add_field(name="Name:", value=random_name, inline=True)
        embed.add_field(name="Age:", value=random_age, inline=True)
        embed.add_field(name="Personality:", value=random_personality, inline=True)
        await ctx.send(embed=embed)

    except FileNotFoundError:
        await ctx.send("Error: names.json not found.")
    except json.JSONDecodeError:
        await ctx.send("Error: names.json is not valid JSON.")
    except ValueError as e:
        await ctx.send(f"Error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")


@bot.command(name="menu")
async def menu(ctx):
    commands_list = """```ini
b!clear       - Clears the queue
b!leave       - Makes the bot leave the voice channel
b!menu        - Shows this help message
b!npc         - Generates a random npc with name and stats
b!next        - Shows the next song in the queue
b!now         - Shows the currently playing song
b!pause       - Pauses the current song
b!repertoire  - Lists all songs in the queue
b!loop        - Toggles queue looping
b!roll        - Roll dice ((number of die)d(sides of die) + modifier)
b!resume      - Resumes the current song
b!sing [url]  - Adds a song to the queue and starts singing
b!skip        - Skips the current song
b!stop        - Stops the current song
b!tavern      - Generates a bot comment with reactions for actions
b!shuffle     - Shuffles the queue
```"""
    await ctx.send(f"**The Bumbling Bard Commands:**\n{commands_list}")

@bot.command(name="clear")
async def clear(ctx):
    player = get_music_player(ctx)
    player.clear_queue()
    await ctx.send("The bard clears their repertoire. 🗑️")


# Regular expression to detect URLs
url_pattern = re.compile(r'https?://\S+')

@bot.command(name="tavern")
async def tavern(ctx):
    player = get_music_player(ctx)
    now_playing = player.current['title'] if player.current else "No music is currently playing."
    message = await ctx.send(f":microphone: **Now playing in the tavern:** {now_playing}\n"
                             ":loud_sound: ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                             "**(skip) (stop) (resume) (leave)**")
    reactions = {
         '⏭️': skip,
         '🛑': stop,
         '▶️': resume,
         '🚪': leave
     }
    for emoji in reactions.keys():
         await message.add_reaction(emoji)
    def check(reaction, user):
         return user != bot.user and reaction.message.id == message.id and str(reaction.emoji) in reactions
    while True:
         try:
             reaction, user = await bot.wait_for('reaction_add', timeout=120.0, check=check)
             await message.remove_reaction(reaction.emoji, user)
             command = reactions[str(reaction.emoji)]
             await command(ctx)
             now_playing = player.current['title'] if player.current else "No music is currently playing."
             await message.edit(content=f":microphone: **Now playing in the tavern:** {now_playing}\n"
                                        ":loud_sound: ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                                        "**(skip) (stop) (resume) (leave)**")
         except asyncio.TimeoutError:
             await ctx.send("The bard has gone silent in the tavern. :notes:")
             break

    def reply_check(m):
         return m.channel == ctx.channel and m.reference and m.reference.message_id == message.id
    try:
         reply_message = await bot.wait_for('message', timeout=120.0, check=reply_check)
         if url_pattern.search(reply_message.content):
             url = reply_message.content.strip()
             await sing(ctx, url=url)

    except asyncio.TimeoutError:
         await ctx.send("No replies were made in time.")

@bot.command(name="roll")
async def roll(ctx, dice_spec: str):
    """Rolls dice according to the specified format: NdS+modifier. Example: b!roll 2d6+3"""
    try:
        match = re.match(r"(\d+)d(\d+)(?:([-+]\d+))?", dice_spec)
        if not match:
            raise ValueError("Invalid dice specification. Use NdS+modifier (e.g., 2d6+3)")

        num_dice = int(match.group(1))
        num_sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        if num_dice <= 0 or num_sides <= 0:
            raise ValueError("Number of dice and sides must be positive integers.")

        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        average = (total - modifier) / num_dice if num_dice else 0  # Handle division by zero
        theoretical_average = ((num_sides + 1) / 2) * num_dice + modifier

        # Truncate individual rolls if number of dice exceeds 20
        if num_dice > 20:
            rolls_display = ", ".join(map(str, rolls[:20])) + ", ..."
        else:
            rolls_display = ", ".join(map(str, rolls))

        embed = discord.Embed(title=f"@{ctx.author.display_name} rolled {dice_spec}", color=discord.Color.blue())
        embed.add_field(name="Individual Rolls:", value=rolls_display, inline=False)
        embed.add_field(name="Total:", value=total, inline=True)
        embed.add_field(name="Average:", value=f"{average:.2f}", inline=True)  # Format to two decimal places
        embed.add_field(name="Theoretical Average (total):", value=f"{theoretical_average:.2f}", inline=True)

        await ctx.send(embed=embed)

    except ValueError as e:
        await ctx.send(f"Error: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

# --- RUN THE BOT ---
bot.run(token)