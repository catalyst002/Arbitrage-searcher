import asyncio
import aiohttp
import sqlite3 as sl
from aiogram import Bot

# Configuration (Consider moving these to a separate config file or environment variables)
BOT_TOKEN = ""
CONV_WITH_BOT_ID = 6666666666
COINS_API_URL = "https://api.coingecko.com/api/v3/coins/{}"

# Initialize bot and database connection
bot = Bot(token=BOT_TOKEN)
db = sl.connect('test.db')

async def fetch_coin_data(session, coin_name):
    async with session.get(COINS_API_URL.format(coin_name)) as response:
        return await response.json()

async def send_message(message):
    await bot.send_message(CONV_WITH_BOT_ID, message)

def update_price_in_db(dbcoinname, base, target, platform, newprice):
    with db:
        result = db.execute('SELECT price FROM {} WHERE pair = ? AND platform = ?'.format(dbcoinname), 
                            (f"{base}/{target}", platform)).fetchone()
        if result:
            oldprice = result[0]
            # Calculate price change and decide if a message should be sent
        else:
            # Insert new price if pair does not exist
            db.execute('INSERT INTO {} (pair, platform, price) VALUES (?, ?, ?)'.format(dbcoinname),
                       (f"{base}/{target}", platform, newprice))

async def process_coin(coin_name):
    async with aiohttp.ClientSession() as session:
        coin_data = await fetch_coin_data(session, coin_name)
        dbcoinname = coin_name.replace("-", "")
        # Iterate through tickers and process them
        for ticker in coin_data.get("tickers", []):
            if ticker["market"]["name"] in ["Uniswap (v3)", "Uniswap (v2)", "Sushiswap"]: # Add more as needed
                update_price_in_db(dbcoinname, ticker["base"], ticker["target"], ticker["market"]["name"], ticker["converted_last"]["usd"])

async def main():
    with open("coins.txt", "r") as f:
        coins = eval(f.read())[:101]  # Consider JSON for safer parsing

    tasks = [process_coin(coin) for coin in coins]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
