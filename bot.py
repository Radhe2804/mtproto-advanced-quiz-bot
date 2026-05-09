import asyncio
import logging
import os
import html
from random import shuffle

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')

app = Client('advanced_quiz_bot', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = AsyncIOMotorClient(MONGO_URI).quizbot

user_states = {}

async def get_or_create_user(user_id: int, username: str):
    user = await db.users.find_one({'user_id': user_id})
    if not user:
        await db.users.insert_one({
            'user_id': user_id,
            'username': username or 'Unknown',
            'high_score': 0,
            'total_score': 0,
            'games_played': 0
        })

async def update_user_stats(user_id: int, score: int):
    await db.users.update_one(
        {'user_id': user_id},
        {'$max': {'high_score': score}, '$inc': {'total_score': score, 'games_played': 1}}
    )

async def get_leaderboard():
    return await db.users.find().sort('high_score', -1).limit(10).to_list(10)

async def fetch_questions(amount: int = 5):
    # Using Open Trivia Database
    import requests
    try:
        r = requests.get(f'https://opentdb.com/api.php?amount={amount}&type=multiple', timeout=10)
        data = r.json()
        if data['response_code'] != 0:
            return None
        questions = []
        for item in data['results']:
            q = html.unescape(item['question'])
            correct = html.unescape(item['correct_answer'])
            incorrect = [html.unescape(i) for i in item['incorrect_answers']]
            options = incorrect + [correct]
            shuffle(options)
            correct_idx = options.index(correct)
            questions.append({'question': q, 'options': options, 'correct_idx': correct_idx})
        return questions
    except Exception as e:
        logger.error(e)
        return None

@app.on_message(filters.command('start'))
async def start(client, message: Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    kb = [
        [InlineKeyboardButton('🎮 Start New Quiz', callback_data='start_quiz')],
        [InlineKeyboardButton('🏆 Leaderboard', callback_data='leaderboard')],
        [InlineKeyboardButton('📊 My Stats', callback_data='my_stats')]
    ]
    await message.reply(
        f"👋 Hi **{message.from_user.first_name}**!\n\n"
        "🚀 **Advanced MTProto Quiz Bot**\n"
        "Native Quiz • MongoDB • High Performance",
        reply_markup=InlineKeyboardMarkup(kb)
    )

@app.on_callback_query(filters.regex('^start_quiz$'))
async def begin_quiz(client, callback):
    await callback.answer()
    questions = await fetch_questions(8)
    if not questions:
        await callback.message.edit_text('Failed to load questions. Try again later.')
        return

    user_states[callback.from_user.id] = {
        'questions': questions,
        'current': 0,
        'score': 0
    }

    q = questions[0]
    await client.send_poll(
        chat_id=callback.message.chat.id,
        question=f"❓ Question 1/{len(questions)}\n\n{q['question']}",
        options=q['options'],
        type='quiz',
        correct_option_id=q['correct_idx'],
        is_anonymous=False,
        explanation='Well done! 🎯'
    )

@app.on_message(filters.poll)
async def handle_quiz_result(client, message: Message):
    poll = message.poll
    if poll.is_closed and message.chat.type == 'private':
        user_id = message.chat.id
        state = user_states.get(user_id)
        if state:
            # Note: In real implementation, you track score incrementally
            final_score = state.get('score', 0) + 1  # Simplified
            await update_user_stats(user_id, final_score)
            await client.send_message(user_id, f"🎉 Quiz Completed!\n\nYour Score: **{final_score}/{len(state['questions'])}**", parse_mode='Markdown')
            if user_id in user_states:
                del user_states[user_id]

# TODO: Add more handlers (leaderboard, stats, category selection)
print('🚀 MTProto Quiz Bot Started!')

async def main():
    await app.start()
    await asyncio.Future()  # Keep running

if __name__ == '__main__':
    asyncio.run(main())
