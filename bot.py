import os
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from mega import Mega

# ✅ Secure API Credentials (Set as Environment Variables)
API_ID = int(os.getenv("API_ID", "29382018"))  # Replace with actual API_ID
API_HASH = os.getenv("API_HASH", "4734a726c04620c61ec0a28a1ae0d57f")  # Replace with actual API_HASH
BOT_TOKEN = os.getenv("BOT_TOKEN", "8022651374:AAHrYl4crOd0EbPIFgvCFiCGoQPaEb1PKDE")  # Replace with actual BOT_TOKEN

# ✅ MEGA Credentials (Optional)
MEGA_EMAIL = os.getenv("MEGA_EMAIL", "4labanibehera@gmail.com")
MEGA_PASSWORD = os.getenv("MEGA_PASSWORD", "@Labani25")

# ✅ File Storage Path
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ✅ Auto-delete old files (Max storage: 10GB)
MAX_STORAGE = 10 * 1024 * 1024 * 1024  # 10GB limit

# ✅ Initialize Bot & MEGA
bot = Client("mega_torrent_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mega = Mega()
m = mega.login(MEGA_EMAIL, MEGA_PASSWORD) if MEGA_EMAIL and MEGA_PASSWORD else None


async def progress_bar(current, total, message: Message):
    """Displays upload progress."""
    percent = (current / total) * 100
    progress = f"📤 Uploading: {int(percent)}% ({current / 1024 / 1024:.2f} MB / {total / 1024 / 1024:.2f} MB)"
    await message.edit_text(progress)


@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Welcome! Send a **MEGA or Torrent link** to download & upload to Telegram.")


@bot.on_message(filters.text)
async def handle_links(client, message):
    link = message.text.strip()

    if "mega.nz" in link:
        await process_mega(client, message, link)
    elif "magnet:" in link:
        await process_torrent(client, message, link)
    else:
        await message.reply_text("❌ **Invalid link!** Send a **MEGA or Magnet link.**")


async def process_mega(client, message, mega_link):
    """Downloads from MEGA."""
    await message.reply_text("🔄 **Downloading from MEGA...**")
    try:
        process = await asyncio.create_subprocess_exec("megadl", mega_link, "--path", DOWNLOAD_PATH)
        await process.communicate()

        files = os.listdir(DOWNLOAD_PATH)
        if not files:
            await message.reply_text("❌ **Download failed!** No file found.")
            return

        file_path = os.path.join(DOWNLOAD_PATH, files[0])
        await handle_large_file(client, message, file_path)

    except Exception as e:
        await message.reply_text(f"❌ **Error:** {str(e)}")


async def process_torrent(client, message, torrent):
    """Downloads from Torrent."""
    await message.reply_text("🔄 **Downloading Torrent...**")
    try:
        process = await asyncio.create_subprocess_exec("aria2c", "-d", DOWNLOAD_PATH, torrent)
        await process.communicate()

        files = os.listdir(DOWNLOAD_PATH)
        if not files:
            await message.reply_text("❌ **Download failed!** No file found.")
            return

        for file in files:
            file_path = os.path.join(DOWNLOAD_PATH, file)
            await handle_large_file(client, message, file_path)

    except Exception as e:
        await message.reply_text(f"❌ **Error:** {str(e)}")


async def handle_large_file(client, message, file_path):
    """Handles large files and uploads to Telegram."""
    file_size = os.path.getsize(file_path)

    if file_size > 2097152000:
        await message.reply_text("⚠️ **File >2GB! Splitting...**")
        split_files = split_large_file(file_path)
        for split_file in split_files:
            await upload_to_telegram(client, message, split_file)
            os.remove(split_file)
    else:
        await upload_to_telegram(client, message, file_path)
        os.remove(file_path)


async def upload_to_telegram(client, message, file_path):
    """Uploads files to Telegram."""
    await message.reply_text("✅ **Uploading to Telegram...**")
    await client.send_document(
        message.chat.id,
        document=file_path,
        caption=f"📂 **{os.path.basename(file_path)}**",
        progress=progress_bar,
    )


def split_large_file(file_path, chunk_size=1900 * 1024 * 1024):
    """Splits large files into chunks."""
    output_files = []
    base_name, ext = os.path.splitext(file_path)
    part = 1
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            split_file = f"{base_name}_part{part}{ext}"
            with open(split_file, "wb") as sf:
                sf.write(chunk)
            output_files.append(split_file)
            part += 1
    return output_files


def get_total_storage_used():
    """Calculates total storage used."""
    return sum(os.path.getsize(os.path.join(DOWNLOAD_PATH, f)) for f in os.listdir(DOWNLOAD_PATH))


def clean_old_files():
    """Deletes old files if storage >10GB."""
    if get_total_storage_used() > MAX_STORAGE:
        files = sorted(os.listdir(DOWNLOAD_PATH), key=lambda f: os.path.getctime(os.path.join(DOWNLOAD_PATH, f)))
        while files and get_total_storage_used() > MAX_STORAGE:
            oldest_file = os.path.join(DOWNLOAD_PATH, files.pop(0))
            os.remove(oldest_file)


# ✅ Auto-delete old files every 1 hour
async def auto_cleaner():
    while True:
        clean_old_files()
        await asyncio.sleep(3600)


async def main():
    await bot.start()
    await auto_cleaner()

if __name__ == "__main__":
    asyncio.run(main())
    
