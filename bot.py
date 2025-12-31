import base64

import asyncio, os, json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import gspread_asyncio
from google.oauth2.service_account import Credentials

load_dotenv()

bot = Bot(os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
CREDS = json.loads(
    base64.b64decode(os.getenv("GOOGLE_CREDS_JSON_BASE64")).decode("utf-8")
)

agcm = gspread_asyncio.AsyncioGspreadClientManager(
    lambda: Credentials.from_service_account_info(
        CREDS,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
)

def parse(text):
    words = text.split()
    number, username, links = None, None, []

    for w in words:
        if "tiktok.com" in w:
            links.append(w)
        elif w.isdigit() and not number:
            number = int(w)
        elif not w.isdigit() and "http" not in w and not username:
            username = w

    return username, number, links

@dp.message()
async def handler(msg: types.Message):
    if not msg.text:
        return

    username, number, links = parse(msg.text)

    if not number or not links:
        return

    client = await agcm.authorize()
    sh = await client.open_by_key(SPREADSHEET_ID)

    if username:
        ws = await sh.worksheet("TEAM")
        await ws.append_row([username, number, " | ".join(links)])
        t = "TEAM"
    else:
        ws = await sh.worksheet("OFFERS")
        await ws.append_row(
            [datetime.now().strftime("%d.%m.%Y %H:%M"), number, " | ".join(links)]
        )
        t = "OFFERS"

    await msg.answer(f"✅ Записано | {t} | {number} | {len(links)}")

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
