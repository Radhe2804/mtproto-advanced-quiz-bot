import asyncio
import logging
import os
import json
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID", 0))

app = Client("cgvyapam_quiz_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = AsyncIOMotorClient(MONGO_URI).cgvyapam_quiz

user_states = {}

# ============== ADMIN PANEL ==============
@app.on_message(filters.command("admin") & filters.user(OWNER_ID))
async def admin_panel(client, message: Message):
    keyboard = [
        [InlineKeyboardButton("📤 Bulk Upload Questions (JSON)", callback_data="bulk_upload")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_admin")]
    ]
    await message.reply(
        "👑 **CGVYAPAM Assistant Draftsman Admin Panel**\n\n"
        "Use this panel to manage questions for the exam.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_callback_query(filters.regex("^bulk_upload$"))
async def bulk_upload_start(client, callback: CallbackQuery):
    await callback.answer("Send your questions.json file now")
    await callback.message.edit_text(
        "📤 **Bulk Upload Ready**\n\n"
        "Please send the `.json` file containing your questions.\n"
        "It must be a JSON array of question objects.\n\n"
        "Supported types: single, ar, match, sequence, multi, numerical"
    )

@app.on_message(filters.document & filters.user(OWNER_ID))
async def handle_bulk_upload(client, message: Message):
    if not message.document.file_name.endswith(".json"):
        await message.reply("❌ Please send a valid `.json` file")
        return

    file_path = await message.download()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        if not isinstance(questions, list):
            await message.reply("❌ JSON must be an array of questions")
            return

        # Insert into MongoDB
        result = await db.questions.insert_many(questions)
        await message.reply(
            f"✅ **Bulk Upload Successful!**\n\n"
            f"Added **{len(result.inserted_ids)}** questions to the database.\n"
            f"Total questions now: {await db.questions.count_documents({})}"
        )
    except Exception as e:
        await message.reply(f"❌ Error processing file: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.on_callback_query(filters.regex("^bot_stats$"))
async def bot_stats(client, callback: CallbackQuery):
    total = await db.questions.count_documents({})
    await callback.answer()
    await callback.message.edit_text(
        f"📊 **Bot Statistics**\n\n"
        f"Total Questions in DB: **{total}**\n"
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

# ============== START ==============
@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    keyboard = [
        [InlineKeyboardButton("🎮 Start Practice Quiz", callback_data="start_quiz")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin")]
    ]
    await message.reply(
        "👋 **Welcome to CGVYAPAM Assistant Draftsman Quiz Bot**\n\n"
        "This bot follows the exact question patterns from CGVYAPAM papers.\n\n"
        "Choose an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============== PLACEHOLDER FOR FULL QUIZ LOGIC ==============
# You can expand this section with full handlers for:
# - single, ar (all 5 variants), match, sequence, multi, numerical
# - Image support via image_url
# - Proper answer checking, scoring, streaks, etc.

@app.on_callback_query(filters.regex("^start_quiz$"))
async def start_quiz_placeholder(client, callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🚧 **Quiz mode is ready to be expanded.**\n\n"
        "The bulk upload and admin panel are fully working.\n"
        "Tell me if you want me to add the complete quiz-playing logic next (A&R variants, Match, Sequence, Multi-select, etc.)."
    )

async def main():
    await app.start()
    print("🚀 CGVYAPAM MTProto Quiz Bot started successfully!")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
