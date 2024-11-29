import json
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from main import cleaners

TOKEN = "8046268758:AAGocfkvqWEB6APk-A2KIeAVHbBT_59QGN0"
GROUP_ID = "-4789467558"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

USERS_FILE = "users.json"
DAILY_FILE = "daily.json"
WEEKLY_FILE = "weekly.json"
LEFT_FILE = "left.json"
ADMIN_IDS = [1178777189, 1274378031, 1872062029]


def chunk_text(text, max_length=4096):
        chunks = []
        while len(text) > max_length:
            split_index = text.rfind("\n", 0, max_length)
            if split_index == -1:
                split_index = max_length
            chunks.append(text[:split_index])
            text = text[split_index:].lstrip()
        chunks.append(text)
        return chunks

class ReadingState(StatesGroup):
    user_name = State()
    book_name = State()
    books = State()
    from_page = State()
    to_page = State()
    finished = State()  
    confirmation = State()


def load_json(file):
    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "r") as f:
        current_data = json.load(f)
    current_data.update(data)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(current_data, f, indent=4)

def save_json2(filepath, data):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

@dp.message_handler(lambda message: str(message.chat.id) == GROUP_ID)
async def ignore_group_messages(message: types.Message):
        return 

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)  # Get the user's ID as a string

    # Load users.json and left.json
    users = load_json(USERS_FILE)
    left_users = load_json(LEFT_FILE)

    # Check if the user exists in left.json
    if user_id in left_users:
        # Move user data from left.json to users.json
        users[user_id] = left_users.pop(user_id)
        save_json(USERS_FILE, users)
        save_json2(LEFT_FILE, left_users)
        msg = "Welcome back to the Book Club Bot! Your data has been restored."
    else:
        # Create a new user if not found in left.json or users.json
        if user_id not in users:
            users[user_id] = {
                "read_pages": 0,
                "penalty": 0,
                "username": message.from_user.username or "N/A",
                "fullname": message.from_user.full_name,
                "user_name": "",
                "finished": [],
                "book": []
            }
            save_json(USERS_FILE, users)
        msg = "Welcome to the Book Club Bot!"

    # Prepare keyboard
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📚 Today Have Read")).add(KeyboardButton("Log Out 🚪"))

    if message.from_user.id in ADMIN_IDS:
        keyboard.add(
            KeyboardButton("📅 Daily Statistics"),
            KeyboardButton("📈 Weekly Statistics"),
            KeyboardButton("👥 User Statistics")
        )

    # Respond to the user
    await message.answer(msg, reply_markup=keyboard)



@dp.message_handler(lambda message: message.text == "📚 Today Have Read")
async def today_read_handler(message: types.Message):
    users = load_json(USERS_FILE)
    user_id = str(message.from_user.id)

    if len(users[user_id].get("user_name")) == 0:
        await message.answer("🧑 Please provide your name:")
        await ReadingState.user_name.set()
    else:
        await message.answer("💣 From Page:")
        await ReadingState.from_page.set()


@dp.message_handler(state=ReadingState.user_name)
async def user_name_handler(message: types.Message, state: FSMContext):
    users = load_json(USERS_FILE)
    user_id = str(message.from_user.id)

    users[user_id]["user_name"] = message.text
    save_json(USERS_FILE, users)

    await state.update_data(user_name=message.text)
    await message.answer("💣 From Page:")
    await ReadingState.from_page.set()


@dp.message_handler(state=ReadingState.book_name)
async def book_name_handler(message: types.Message, state: FSMContext):
    await ReadingState.to_page.set()
    if message.text == "Add new one ➕":
        await message.answer("Please provide the name of the book you have read:", reply_markup=ReplyKeyboardRemove())
    else:
       await to_page_handler(message, state)

@dp.message_handler(state=ReadingState.from_page)
async def from_page_handler(message: types.Message, state: FSMContext):
    try:
        from_page = int(message.text)
    except ValueError:
        await message.answer("Invalid page number. Try again.")
        return
    await state.update_data(from_page=from_page)
    await message.answer("💣 To Page:")
    await ReadingState.books.set()

@dp.message_handler(state=ReadingState.books)
async def books_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        to_page = int(message.text)
        if to_page - data['from_page'] < 0:
            await message.answer("Invalid page range. Try again.")
            return 
        await state.update_data(to_page=to_page)
    except ValueError:
        await message.answer("Invalid page number. Try again.")
        return
    users = load_json(USERS_FILE)
    if len(users[str(message.from_user.id)]['book']) == 0:
        await message.answer("Please provide the name of the book you have read:")
        await ReadingState.to_page.set()
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in users[str(message.from_user.id)]['book']:
            keyboard.add(i)
        keyboard.add('Add new one ➕')
        await message.answer('Choose from these books or add the new one', reply_markup=keyboard)
        await ReadingState.book_name.set()
    


@dp.message_handler(state=ReadingState.to_page)
async def to_page_handler(message: types.Message, state: FSMContext):
    users = load_json(USERS_FILE)
    if message.text not in users[str(message.from_user.id)]['book']:
        users[str(message.from_user.id)]['book'].append(message.text)  
        save_json(USERS_FILE, users)

    await state.update_data(book_name=message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("✅ Yes"), KeyboardButton("❌ No"))
    await message.answer("Have you finished reading the book?", reply_markup=keyboard)
    await ReadingState.finished.set()

@dp.message_handler(lambda message: message.text in ["✅ Yes", "❌ No"], state=ReadingState.finished)
async def finished_handler(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users = load_json(USERS_FILE)
    data = await state.get_data()
    read_pages = data['to_page'] - data['from_page']

    daily = load_json(DAILY_FILE)
    if user_id not in daily:
        daily[user_id] = {"read_pages": read_pages}
    else:
        daily[user_id]["read_pages"] += read_pages
    save_json(DAILY_FILE, daily)
    
    # Set user_name and book_name if missing
    data['user_name'] = data.get("user_name", users[user_id]['user_name'])
    data['book_name'] = data.get("book_name", "Unknown Book")
    
    # Prepare message for confirmation
    confirmation_text = (
        f"👤 Reader name: {data['user_name']}\n"
        f"📚 Book name: {data['book_name']}\n"
        f"💣 From Page: {data['from_page']}\n"
        f"💣 To Page: {data['to_page']}\n"
        f"💣 Overall: {read_pages}\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y')}\n"
        f"Finished: {message.text} \n"
        f"#challange\n"
        f"Do you want to send this information to the group? ✅ Yes / ❌ No"
    )
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("✅ Yes"), KeyboardButton("❌ No"))
    
    await message.answer(confirmation_text, reply_markup=keyboard)
    await ReadingState.confirmation.set()


@dp.message_handler(lambda message: message.text in ["✅ Yes", "❌ No"], state=ReadingState.confirmation)
async def confirmation_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = str(message.from_user.id)
    users = load_json(USERS_FILE)


    if message.text == "✅ Yes":
        data['user_name'] = data.get("user_name", users[user_id]['user_name'])
        data['book_name'] = data.get("book_name", "Unknown Book")
        text = (
            f"👤 Reader name: {data['user_name']}\n"
            f"📚 Book name: {data['book_name']}\n"
            f"💣 From Page: {data['from_page']}\n"
            f"💣 To Page: {data['to_page']}\n"
            f"💣 Overall: {data['to_page'] - data['from_page']}\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y')}\n"
            f"Finished: {data.get('finished', '❌ No')}\n"
            f"📩 @Di_Baudelaire\n"
            f"#challange"
        )
        await bot.send_message(GROUP_ID, text)

        # Update user data if the book is finished
        if{data.get('finished', '❌ No')} != '❌ No':
            users[user_id]["finished"].append(data['book_name'])
            if data['book_name'] in users[user_id]["book"]:
                users[user_id]["book"].remove(data['book_name'])
            save_json(USERS_FILE, users)
            await message.answer(f"Congratulations on finishing the book: {data['book_name']}! 🎉")
        else:
            await message.answer("Keep going! You'll finish it soon! 💪")
            if data['book_name'] not in users[user_id]["book"]:
                users[user_id]["book"].append(data["book_name"])
            save_json(USERS_FILE, users)

    else:
        # Redirect to start handler
        await message.answer("No problem! Let's start again.")
        await state.finish()
        await start_handler(message)
    
    await state.finish()


@dp.message_handler(lambda message: message.text == "Log Out 🚪")
async def logout(message: types.Message):
    user_id = str(message.from_user.id) 
    
    try:
        with open("users.json", "r") as users_file:
            users_data = json.load(users_file)
            user_data = users_data.pop(user_id)
            
            try:
                with open("left.json", "r") as left_file:
                    left_data = json.load(left_file)
            except FileNotFoundError:
                left_data = {}

            left_data[user_id] = user_data

            with open("users.json", "w") as users_file:
                json.dump(users_data, users_file, indent=4)

            with open("left.json", "w") as left_file:
                json.dump(left_data, left_file, indent=4)

                keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add(KeyboardButton("/start"))
            
            await message.reply("You have successfully logged out. All your data has been moved to the archive. Goodbye! 👋", reply_markup=keyboard)

    
    except Exception as e:
        await message.reply("An error occurred while processing your request. Please try again later.")



@dp.message_handler(lambda message: message.text == "📅 Daily Statistics" and message.from_user.id in ADMIN_IDS)
async def daily_statistics_handler(message: types.Message):
    daily = load_json(DAILY_FILE)
    users = load_json(USERS_FILE)
    stats = "\n".join([
    f'🧍 {users.get(user_id, {}).get("user_name", "Unknown User")}: '
    f'{"Penalty (@" + users[user_id]["username"] + ") 5000 ❌"  if daily.get(user_id, {}).get("read_pages", 5000) == 5000 or daily.get(user_id, {}).get("read_pages", 0) < 11 else str(daily.get(user_id, {}).get("read_pages")) + " pages ✅"} \n'
    for user_id in users
])
    if stats:
        message_chunks = chunk_text(f"📅 Daily Statistics:\n{stats}")
        for chunk in message_chunks:
            await message.answer(chunk)
    else:
        await message.answer("No data available.")


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
    if stats:
        message_chunks = chunk_text(f"📈 Weekly Statistics:\n{stats}")
        for chunk in message_chunks:
            await message.answer(chunk)
    else:
        await message.answer("No data available.")


@dp.message_handler(lambda message: message.text == "👥 User Statistics" and message.from_user.id in ADMIN_IDS)
async def user_statistics_handler(message: types.Message):

    users = load_json(USERS_FILE)
    stats = "\n".join(
        [
            f" --------- \n"
            f"🧍{users[user_id]['user_name'] if len(users[user_id]['user_name']) != 0 else users[user_id]['fullname']}:\n"
            f"  pages 📑: {data['read_pages']} \n"
            f"  Total Penalty: {data['penalty']} 🚫 \n"
            f"  Finished Books: \n" + ("\n".join([f"📖 {book}" for book in data['finished']]) if data['finished'] else 'No books finished yet') + "\n"
            f"  Still Reading: \n" + ("\n".join([f"📖 {book}" for book in data['book']]) if data['book'] else 'No books chosen yet')
            for user_id, data in users.items()
        ]
    )

    if stats:
        message_chunks = chunk_text(f"👥 User Statistics:\n{stats}")
        for chunk in message_chunks:
            await message.answer(chunk)
    else:
        await message.answer("No data available.")


async def on_start(dp):
    asyncio.create_task(cleaners())

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_start)
