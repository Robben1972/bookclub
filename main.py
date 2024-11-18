import asyncio
import datetime
import json

from aiogram import Bot


TOKEN = "8046268758:AAGocfkvqWEB6APk-A2KIeAVHbBT_59QGN0"

USERS_FILE = "users.json"
DAILY_FILE = "daily.json"
WEEKLY_FILE = "weekly.json"
GROUP_ID = "-1002125753894"
bot = Bot(token=TOKEN)


def load_json(file):
    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "r") as f:
        current_data = json.load(f)
    current_data.update(data)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(current_data, f, indent=4)

def clear_json(file):
    with open(file, "w") as f:
        json.dump({}, f, indent=4)


async def clean_daily():
    users = load_json(USERS_FILE)
    daily = load_json(DAILY_FILE)
    weekly = load_json(WEEKLY_FILE)

    for user_id, user_data in users.items():
        if user_id in daily:
            pages = daily[user_id]["read_pages"]
            if user_id in weekly:
                if pages >= 20:
                    weekly[user_id]["read_pages"] += pages
                else:
                    weekly[user_id]["penalty"] += 5000
            else:
                weekly[user_id] = {
                    "read_pages": pages if pages >= 20 else 0,
                    "penalty": 5000 if pages < 20 else 0,
                    "username": user_data["username"],
                    "fullname": user_data["fullname"],
                    "user_name": user_data["user_name"],
                }
        else:
            if user_id in weekly:
                weekly[user_id]["penalty"] += 5000
            else:
                weekly[user_id] = {
                    "read_pages": 0,
                    "penalty": 5000,
                    "username": user_data["username"],
                    "fullname": user_data["fullname"],
                    "user_name": user_data["user_name"],
                }

    stats = "\n".join([
    f'🧍 {users.get(user_id, {}).get("user_name", "Unknown User")}: '
    f'{"Penalty (@" + users[user_id]["username"] + ") 5000 ❌"  if daily.get(user_id, {}).get("read_pages", 5000) == 5000 or daily.get(user_id, {}).get("read_pages", 0) < 20 else str(daily.get(user_id, {}).get("read_pages")) + " pages ✅"} \n'
    for user_id in users
])

    await bot.send_message(GROUP_ID, stats)

    save_json(WEEKLY_FILE, weekly)
    clear_json(DAILY_FILE)


async def clean_weekly():
    weekly = load_json(WEEKLY_FILE)
    users = load_json(USERS_FILE)

    best_reader = max(weekly.items(), key=lambda x: x[1]["read_pages"], default=None)
    if best_reader:
        user_id, stats = best_reader
        text = (
            f"The best reader of this week is {stats['fullname']}, "
            f"who has read {stats['read_pages']} pages. "
            f"Congrats @{stats['username']}!"
        )
        await bot.send_message(GROUP_ID, text)

    for user_id, stats in weekly.items():
        if user_id in users:
            users[user_id]["read_pages"] += stats["read_pages"]
            users[user_id]["penalty"] += stats["penalty"]

    save_json(USERS_FILE, users)
    clear_json(WEEKLY_FILE)


async def main():
        current_time = datetime.datetime.now().time()

        if current_time.hour == 8 and current_time.minute == 55:
            await clean_daily()

        if current_time.hour == 9 and current_time.minute == 0 and datetime.datetime.now().weekday() == 5:  # 5 is Saturday
            await clean_weekly()



async def cleaners():
    while True:
        await main()
        await asyncio.sleep(60)
