import json
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from main import cleaners

TOKEN = "8046268758:AAGocfkvqWEB6APk-A2KIeAVHbBT_59QGN0"
GROUP_ID = "-1002125753894"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

USERS_FILE = "users.json"
DAILY_FILE = "daily.json"
WEEKLY_FILE = "weekly.json"
ADMIN_IDS = [1178777189, 1274378031, 1872062029]


class ReadingState(StatesGroup):
    user_name = State()
    book_name = State()
    from_page = State()
    to_page = State()
    finished = State()  


def load_json(file):
    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "r") as f:
        current_data = json.load(f)
    current_data.update(data)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(current_data, f, indent=4)


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    users = load_json(USERS_FILE)
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {
            "read_pages": 0,
            "penalty": 0,
            "username": message.from_user.username or "N/A",
            "fullname": message.from_user.full_name,
            "user_name" : "",
            "finished": [],
            "book" : ""
        }
        save_json(USERS_FILE, users)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📚 Today Have Read"))

    # Add statistics buttons only for admins
    if message.from_user.id in ADMIN_IDS:
        keyboard.add(
            KeyboardButton("📅 Daily Statistics"),
            KeyboardButton("📈 Weekly Statistics"),
            KeyboardButton("👥 User Statistics")
        )

    await message.answer("Welcome to the Book Club Bot!", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "📚 Today Have Read")
async def today_read_handler(message: types.Message):
    users = load_json(USERS_FILE)
    user_id = str(message.from_user.id)

    # Check if the user's name is already set
    if len(users[user_id].get("user_name")) == 0:
        await message.answer("🧑 Please provide your name:")
        await ReadingState.user_name.set()
    elif len(users[user_id].get("book")) == 0:
        await message.answer("📚 Book name:")
        await ReadingState.book_name.set()
    else:
        await message.answer("💣 From Page:")
        await ReadingState.from_page.set()


@dp.message_handler(state=ReadingState.user_name)
async def user_name_handler(message: types.Message, state: FSMContext):
    users = load_json(USERS_FILE)
    user_id = str(message.from_user.id)

    # Update the user's name in the users.json file
    users[user_id]["user_name"] = message.text
    save_json(USERS_FILE, users)

    # Continue to ask for the book name
    await state.update_data(user_name=message.text)
    await message.answer("📚 Book name:")
    await ReadingState.book_name.set()


@dp.message_handler(state=ReadingState.book_name)
async def book_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(book_name=message.text)
    await message.answer("💣 From Page:")
    await ReadingState.from_page.set()


@dp.message_handler(state=ReadingState.from_page)
async def from_page_handler(message: types.Message, state: FSMContext):
    try:
        from_page = int(message.text)
    except ValueError:
        await message.answer("Invalid page number. Try again.")
        return
    await state.update_data(from_page=from_page)
    await message.answer("💣 To Page:")
    await ReadingState.to_page.set()


@dp.message_handler(state=ReadingState.to_page)
async def to_page_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        to_page = int(message.text)
    except ValueError:
        await message.answer("Invalid page number. Try again.")
        return
    await state.update_data(to_page=to_page)

    # Ask if the user has finished the book
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("✅ Yes"), KeyboardButton("❌ No"))
    await message.answer("Have you finished reading the book?", reply_markup=keyboard)
    await ReadingState.finished.set()  # Move to the next state to capture the "finished" answer

@dp.message_handler(lambda message: message.text in ["✅ Yes", "❌ No"], state=ReadingState.finished)
async def finished_handler(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users = load_json(USERS_FILE)
    data = await state.get_data()
    read_pages = data['to_page'] - data['from_page']
    if read_pages < 0:
        await message.answer("Invalid page range. Try again.")
        return

    daily = load_json(DAILY_FILE)
    users = load_json(USERS_FILE)
    user_id = str(message.from_user.id)
    if user_id not in daily:
        daily[user_id] = {"read_pages": read_pages}
    else:
        daily[user_id]["read_pages"] += read_pages
    save_json(DAILY_FILE, daily)
    
    try: 
        data['user_name'] = data["user_name"]
    except:
        data['user_name'] = users[user_id]['user_name']
    try: 
        data['book_name'] = data["book_name"]
    except:
        data['book_name'] = users[user_id]['book']
    
    text = (
        f"👤 Reader name: {data['user_name']}\n"
        f"📚 Book name: {data['book_name']}\n"
        f"💣 From Page: {data['from_page']}\n"
        f"💣 To Page: {data['to_page']}\n"
        f"💣 Overall: {read_pages}\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y')}\n"
        f"Finished: {message.text} \n"
        f"📩 @Di_Baudelaire\n"
        f"#challange"
    )
    await bot.send_message(GROUP_ID, text)

    if message.text == "✅ Yes":
        book_name = data['book_name']
        if book_name and book_name not in users[user_id]["finished"]:
            users[user_id]["finished"].append(book_name)
            users[user_id]["book"] = ""
            save_json(USERS_FILE, users)
            await message.answer(f"Congratulations on finishing the book: {book_name}! 🎉")
        else:
            await message.answer("It seems like you have already finished this book")
    else:
        await message.answer("Keep going, you'll finish it soon! 💪")
        users[user_id]["book"] = data["book_name"]
        save_json(USERS_FILE, users)

    await state.finish()
    await start_handler(message)


@dp.message_handler(lambda message: message.text == "📅 Daily Statistics" and message.from_user.id in ADMIN_IDS)
async def daily_statistics_handler(message: types.Message):
    daily = load_json(DAILY_FILE)
    users = load_json(USERS_FILE)
    stats = "\n".join([
    f'🧍 {users.get(user_id, {}).get("user_name", "Unknown User")}: '
    f'{"Penalty (@" + users[user_id]["username"] + ") 5000 ❌"  if daily.get(user_id, {}).get("read_pages", 5000) == 5000 or daily.get(user_id, {}).get("read_pages", 0) < 20 else str(daily.get(user_id, {}).get("read_pages")) + " pages ✅"} \n'
    for user_id in users
])
    await message.answer(f"📅 Daily Statistics:\n{stats or 'No data available.'}")


@dp.message_handler(lambda message: message.text == "📈 Weekly Statistics" and message.from_user.id in ADMIN_IDS)
async def weekly_statistics_handler(message: types.Message):
    weekly = load_json(WEEKLY_FILE)
    users = load_json(USERS_FILE)
    
    stats = "\n".join(
        [
            f" --------- \n"
            f"🧍{users[user_id]['user_name'] if len(users[user_id]['user_name']) != 0 else users[user_id]['fullname']}:\n"
            f"  pages 📑: {weekly[user_id]['read_pages'] if user_id in weekly else 0} \n"
            f"  Total Penalty: {weekly[user_id]['penalty'] if user_id in weekly else 0} 🚫 \n"
            for user_id, data in users.items()
        ]
    )
    await message.answer(f"📈 Weekly Statistics:\n{stats or 'No data available.'}")


@dp.message_handler(lambda message: message.text == "👥 User Statistics" and message.from_user.id in ADMIN_IDS)
async def user_statistics_handler(message: types.Message):
    users = load_json(USERS_FILE)
    stats = "\n".join(
        [
            f" --------- \n"
            f"🧍{users[user_id]['user_name'] if len(users[user_id]['user_name']) != 0 else users[user_id]['fullname']}:\n"
            f"  pages 📑: {data['read_pages']} \n"
            f"  Total Penalty: {data['penalty']} 🚫 \n"
            f"  Finished Books: \n" + ("\n".join([f"📖 {book}" for book in data['finished']]) if data['finished'] else 'No books finished yet')
            for user_id, data in users.items()
        ]
    )
    await message.answer(f"👥 User Statistics:\n{stats or 'No data available.'}")


async def on_start(dp):
    asyncio.create_task(cleaners())

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_start)
