import os
import asyncio
import subprocess
from tqdm import tqdm
from pyrogram import Client, filters
from pyrogram.types import Message
from mega import Mega

# ✅ Telegram API Credentials
API_ID = "29382018"
API_HASH = "4734a726c04620c61ec0a28a1ae0d57f"
BOT_TOKEN = "8022651374:AAHrYl4crOd0EbPIFgvCFiCGoQPaEb1PKDE"

# ✅ MEGA Credentials (Optional, but improves reliability)
MEGA_EMAIL = "4labanibehera@gmail.com"
MEGA_PASSWORD = "@Labani25"

# ✅ File Storage Path
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ✅ Auto-delete old files (Max storage: 10GB)
MAX_STORAGE = 10 * 1024 * 1024 * 1024  # 10GB limit

# ✅ Initialize Bot & MEGA
bot = Client("mega_torrent_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mega = Mega()
m = mega.login(MEGA_EMAIL, MEGA_PASSWORD)

# ✅ Progress Callback for Uploads
async def progress_bar(current, total, message: Message):
    percent = (current / total) * 100
    progress = f"📤 Uploading: {int(percent)}% ({current / 1024 / 1024:.2f} MB / {total / 1024 / 1024:.2f} MB)"
    await message.edit(progress)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("👋 Welcome! Send me a **MEGA link or Torrent file/magnet link**, and I'll **download & upload** it to Telegram.")

@bot.on_message(filters.text)
async def handle_links(client, message):
    link = message.text.strip()

    if "mega.nz" in link:
        await process_mega(client, message, link)
    elif "magnet:" in link:
        await process_torrent(client, message, link)
    else:
        await message.reply("❌ **Invalid link!** Send a **MEGA link or a Magnet link.**")

@bot.on_message(filters.document)
async def handle_torrent_file(client, message):
    if message.document.file_name.endswith(".torrent"):
        torrent_path = await message.download(DOWNLOAD_PATH)
        await process_torrent(client, message, torrent_path)
    else:
        await message.reply("❌ **Only .torrent files are supported.**")

async def process_mega(client, message, mega_link):
    await message.reply("🔄 **Downloading from MEGA...**")

    try:
        cmd = f"megadl '{mega_link}' --path {DOWNLOAD_PATH}"
        subprocess.run(cmd, shell=True, check=True)

        downloaded_files = os.listdir(DOWNLOAD_PATH)
        if not downloaded_files:
            await message.reply("❌ **Download failed!** No file found.")
            return

        file_path = os.path.join(DOWNLOAD_PATH, downloaded_files[0])
        await handle_large_file(client, message, file_path)

    except Exception as e:
        await message.reply(f"❌ **Error:** {str(e)}")

async def process_torrent(client, message, torrent):
    await message.reply("🔄 **Downloading Torrent...**")

    try:
        cmd = f"aria2c -d {DOWNLOAD_PATH} '{torrent}'"
        subprocess.run(cmd, shell=True, check=True)

        downloaded_files = os.listdir(DOWNLOAD_PATH)
        if not downloaded_files:
            await message.reply("❌ **Download failed!** No file found.")
            return

        for file_name in downloaded_files:
            file_path = os.path.join(DOWNLOAD_PATH, file_name)
            await handle_large_file(client, message, file_path)

    except Exception as e:
        await message.reply(f"❌ **Error:** {str(e)}")

async def handle_large_file(client, message, file_path):
    file_size = os.path.getsize(file_path)

    if file_size > 2097152000:
        await message.reply("⚠️ **File is too large (>2GB)! Splitting it...**")
        split_files = split_large_file(file_path)
        for split_file in split_files:
            await upload_to_telegram(client, message, split_file)
            os.remove(split_file)
    else:
        await upload_to_telegram(client, message, file_path)
        os.remove(file_path)

async def upload_to_telegram(client, message, file_path):
    await message.reply("✅ **Download Complete! Uploading to Telegram...**")
    await client.send_document(
        message.chat.id,
        document=file_path,
        caption=f"📂 **{os.path.basename(file_path)}**",
        progress=progress_bar,
    )

def split_large_file(file_path, chunk_size=1900 * 1024 * 1024):
    """Splits files larger than 2GB into smaller chunks."""
    output_files = []
    base_name, ext = os.path.splitext(file_path)
    part = 1
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            split_file_path = f"{base_name}_part{part}{ext}"
            with open(split_file_path, "wb") as sf:
                sf.write(chunk)
            output_files.append(split_file_path)
            part += 1
    return output_files

def get_total_storage_used()
    """Check total storage used in the downloads folder."""
    total_size = sum(os.path.getsize(os.path.join(DOWNLOAD_PATH, f)) for f in os.listdir(DOWNLOAD_PATH))
    return total_size

def clean_old_files():
    """Deletes oldest files if storage exceeds limit."""
    total_used = get_total_storage_used()
    if total_used > MAX_STORAGE:
        files = sorted(os.listdir(DOWNLOAD_PATH), key=lambda f: os.path.getctime(os.path.join(DOWNLOAD_PATH, f)))
        while total_used > MAX_STORAGE and files:
            oldest_file = os.path.join(DOWNLOAD_PATH, files.pop(0))
            total_used -= os.path.getsize(oldest_file)
            os.remove(oldest_file)

# ✅ Auto-delete old files every 1 hour
async def auto_cleaner():
    while True:
        clean_old_files()
        await asyncio.sleep(3600)

async def main():
    await bot.start()
    await auto_cleaner()

bot.run()
