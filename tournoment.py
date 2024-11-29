import asyncio
import logging
import doctest
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import sys

API_TOKEN = '8046268758:AAGocfkvqWEB6APk-A2KIeAVHbBT_59QGN0'  # Replace with your bot's API token

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Define states
class FormState(StatesGroup):
    code = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Send me the logic of the function (e.g., `return x + 2`).")

@dp.message_handler(state='*', commands=['cancel'])
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("Cancelled. Send me the logic of the function again.")

import io

@dp.message_handler(state='*')
async def get_code(message: types.Message, state: FSMContext):
    code_logic = message.text.strip()
    await state.update_data(code=code_logic)

    # Create the function dynamically
    function_code = f"""
def add_two(x):
    \"\"\"
    >>> add_two(5)
    7
    >>> add_two(0)
    2
    >>> add_two(-5)
    -3
    \"\"\"
    {code_logic}
    """

    # Capture the doctest output
    output = io.StringIO()
    try:
        # Execute the function code
        exec(function_code, globals())
        
        # Redirect the standard output to capture doctest results
        old_stdout = sys.stdout
        sys.stdout = output
        
        # Run the doctest
        doctest.run_docstring_examples(add_two, globals(), name='add_two', optionflags=doctest.ELLIPSIS)
        
        # Restore the standard output
        sys.stdout = old_stdout
        
        # Get captured output
        results = output.getvalue()
        if len(results) != 0:
            raise Exception
        await message.reply(f"Your code passed the tests successfully!\n\nResults:\n{results}")
    except Exception as e:
        sys.stdout = old_stdout
        await message.reply(f"There was an error in your code:\n{str(e)}")
    finally:
        output.close()
    
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)