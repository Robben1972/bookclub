import logging
import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

# Replace 'YOUR_BOT_TOKEN' with your actual Telegram bot API key
API_TOKEN = '7503387130:AAER4rZXoz9PSL8U7wKuV4tpHRP12PABMDs'

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: Message):
    # Get the chat ID
    chat_id = message.chat.id
    # Send the chat ID back to the group
    await message.reply(f'This group ID is: {chat_id}')

async def main() -> None:
    await dp.start_polling(bot) 


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
