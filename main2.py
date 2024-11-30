import json
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from main import cleaners
from environs import Env

env = Env()
env.read_env()

TOKEN = env('TOKEN')
GROUP_ID = env('GROUP_ID')

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

USERS_FILE = env('USERS_FILE')
DAILY_FILE = env('DAILY_FILE')
WEEKLY_FILE = env('WEEKLY_FILE')
LEFT_FILE = env('LEFT_FILE')
BOOKS_FILE = env('BOOKS_FILE')

ADMIN_IDS = [int(env('ADMIN1')), int(env('ADMIN2')) ,int(env("ADMIN3")) ]


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

class UploadBook(StatesGroup):
    book_name = State()

class ReadBook(StatesGroup):
    book_name = State()


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


@dp.message_handler(commands=['test'])
async def get_id(message: types.Message):
    print(message.chat.id)
@dp.message_handler(lambda message: str(message.chat.id) == GROUP_ID)
async def ignore_group_messages(message: types.Message):
        return 

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)

    users = load_json(USERS_FILE)
    left_users = load_json(LEFT_FILE)

    if user_id in left_users:
        users[user_id] = left_users.pop(user_id)
        save_json(USERS_FILE, users)
        save_json2(LEFT_FILE, left_users)
        msg = "Welcome back to the Book Club Bot! Your data has been restored."
    else:
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

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📚 Today Have Read")).add(KeyboardButton("Log Out 🚪"), KeyboardButton("💻 E-library"))

    if message.from_user.id in ADMIN_IDS:
        keyboard.add(
            KeyboardButton("📅 Daily Statistics"),
            KeyboardButton("📈 Weekly Statistics"),
            KeyboardButton("👥 User Statistics"),
            KeyboardButton("Delete User"), KeyboardButton("Upload book")
        )

    # Respond to the user
    await message.answer(msg, reply_markup=keyboard)



@dp.message_handler(lambda message: message.text == "⬅️ Back", state="*")
async def back_handler(message: types.Message, state: FSMContext):
    await start_handler(message)
    await state.finish()

@dp.message_handler(lambda message: message.text == "📚 Today Have Read")
async def today_read_handler(message: types.Message):
    users = load_json(USERS_FILE)
    user_id = str(message.from_user.id)

    if len(users[user_id].get("user_name")) == 0:
        await message.answer("🧑 Please provide your name:")
        await ReadingState.user_name.set()
    else:
        await message.answer("💣 From Page:", reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True).add(KeyboardButton("⬅️ Back")))
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
    
    data['user_name'] = data.get("user_name", users[user_id]['user_name'])
    data['book_name'] = data.get("book_name", "Unknown Book")
    
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
    await state.update_data(finished=message.text)
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
            f"Finished: {data['finished']}\n"
            f"📩 @Di_Baudelaire\n"
            f"#challange"
        )
        await bot.send_message(GROUP_ID, text)
        if data['finished'] != '❌ No':
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
        await start_handler(message)


    else:
        await message.answer("No problem! Let's start again.")
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
    f'{"Penalty (@" + users[user_id]["username"] + ") 5000 ❌"  if daily.get(user_id, {}).get("read_pages", 5000) == 5000 or daily.get(user_id, {}).get("read_pages", 0) < 10 else str(daily.get(user_id, {}).get("read_pages")) + " pages ✅"} \n'
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


@dp.message_handler(lambda message: message.text == "Delete User" and message.from_user.id in ADMIN_IDS)
async def delete_user(message: types.Message):
    users = load_json(USERS_FILE)
    if not users:
        await message.reply("No users found in the database.")
        return

    keyboard = InlineKeyboardMarkup(row_width=2)
    for user_id, user_data in users.items():
        button = InlineKeyboardButton(
            text=user_data.get("user_name", "Unknown User"),
            callback_data=f"delete_user:{user_id}"
        )
        keyboard.add(button)

    await message.reply("Select a user to delete:", reply_markup=keyboard)

@dp.callback_query_handler(lambda callback: callback.data.startswith("delete_user:"))
async def confirm_deletion(callback: types.CallbackQuery):
    user_id = callback.data.split(":")[1]
    users = load_json(USERS_FILE)

    if user_id in users:
        deleted_user_name = users[user_id].get("user_name", "Unknown User")
        del users[user_id]
        save_json2(USERS_FILE, users)
        await callback.message.edit_text(f"User '{deleted_user_name}' has been deleted successfully.")
    else:
        await callback.message.edit_text("User not found in the database.")

@dp.message_handler(lambda message: message.text == "Upload book" and message.from_user.id in ADMIN_IDS)
async def upload_book(message: types.Message, state: FSMContext):
    await message.answer('Please send the book (pls renemae the file before sending it because we automatically use the file name as a book name)', reply_markup=ReplyKeyboardMarkup(
            resize_keyboard=True).add(KeyboardButton("⬅️ Back")))
    await UploadBook.book_name.set()

@dp.message_handler(content_types=['document'], state=UploadBook.book_name)
async def book_name_handler(message: types.Message, state: FSMContext):
    save_json(BOOKS_FILE, {message.document.file_name.split('.')[0]: message.document.file_id})
    await state.finish()
    await start_handler(message)

@dp.message_handler(lambda message: message.text == "💻 E-library")
async def book_library_handler(message: types.Message, state: FSMContext):
    books = load_json(BOOKS_FILE)
    if len(books) > 0:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)  # Ensure keyboard resizes properly
        row = []
        i = 0
        for book_name in books.keys():
            button = KeyboardButton(text=book_name)
            row.append(button)
            i += 1
            if i == 2:  
                keyboard.add(*row)
                row = []
                i = 0
        if row:  
            keyboard.add(*row)
        keyboard.add('⬅️ Back')
        await message.answer("Select a book to read:", reply_markup=keyboard)
        await ReadBook.book_name.set()
    else:
        await message.answer("No books found in the library.")
        await start_handler(message)

@dp.message_handler(state=ReadBook.book_name)
async def get_book(message: types.Message, state: FSMContext):
    books = load_json(BOOKS_FILE)
    if message.text in books:
        book_id = books[message.text]
        await message.answer_document(book_id)
    else:
        await message.answer("Book not found in the library.")
    await state.finish()
    await start_handler(message)




async def on_start(dp):
    asyncio.create_task(cleaners())

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_start)
