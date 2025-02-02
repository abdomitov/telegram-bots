token = "TOKEN"

import os
import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define the download function
def download_video(url, output_dir="downloads"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        return file_path

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a video link, and I'll download it for you.")

# Video link handler
async def handle_video_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id

    try:
        await update.message.reply_text("Downloading your video. Please wait...")
        video_path = download_video(url)

        with open(video_path, 'rb') as video_file:
            await context.bot.send_video(chat_id=chat_id, video=InputFile(video_file))

        os.remove(video_path)  # Clean up the downloaded file
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        await update.message.reply_text("Failed to download the video. Please check the link and try again.")

# Main function to run the bot
async def main():
    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your bot's API token
    TOKEN = token

    # Create the application
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_link))

    # Run the bot
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    import nest_asyncio

    # Apply nested asyncio if event loop is already running
    nest_asyncio.apply()

    # Get the running loop
    loop = asyncio.get_event_loop()

    # Run the main coroutine in the existing loop
    loop.run_until_complete(main())
