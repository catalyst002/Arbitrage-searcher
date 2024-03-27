import asyncio
import json
import sqlite3 as sl
from decimal import Decimal, getcontext
import aiohttp

# Set decimal precision
getcontext().prec = 3

# Initialize database connection
db = sl.connect('test.db')


def setup_database():
    with db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                xsymbol TEXT,
                ysymbol TEXT,
                xchangename TEXT,
                ychangename TEXT,
                diff REAL
            );
        """)


def insert_data(coinname, xsymbol, ysymbol, xchangename, ychangename, diffcheck):
    with db:
        sql = 'INSERT INTO deals (xsymbol, ysymbol, xchangename, ychangename, diff) VALUES (?, ?, ?, ?, ?)'
        db.execute(sql, (xsymbol, ysymbol, xchangename, ychangename, diffcheck))


def get_proxy(proxies, counter):
    return proxies[counter % len(proxies)]


async def fetch_coin_data(session, coin, proxy):
    url = f'https://api.cryptorank.io/v0/coins/{coin}/tickers?includeQuote=false'
    async with session.get(url, proxy=f"http://{proxy}") as response:
        return await response.json()


async def process_coins(minspread, maxspread, proxies):
    setup_database()

    with open('coins.txt', 'r') as f, open('proxy.txt', 'r') as p:
        coins = f.read().splitlines()
        proxies = p.read().splitlines()

    async with aiohttp.ClientSession() as session:
        for idx, coin in enumerate(coins):
            proxy = get_proxy(proxies, idx)
            jsonresp = await fetch_coin_data(session, coin, proxy)
            dataarray = jsonresp.get('data', [])
            await compare_prices(minspread, maxspread, dataarray)


async def compare_prices(minspread, maxspread, dataarray):
    for x in dataarray:
        for y in dataarray:
            try:
                diffcheck = calculate_diffcheck(x, y)
                if criteria_met(diffcheck, minspread, maxspread, x, y):
                    insert_data(
                        x['coinName'], x['symbol'], y['symbol'], x['exchangeName'],
                        y['exchangeName'], diffcheck
                    )
            except (ZeroDivisionError, KeyError):
                continue


def calculate_diffcheck(x, y):
    xprice, yprice = Decimal(x['usdLast']), Decimal(y['usdLast'])
    diff = abs(xprice - yprice)
    percent = (diff / xprice) * 100
    totalspread = x.get('spread', 0) + y.get('spread', 0)
    return percent - totalspread


def criteria_met(diffcheck, minspread, maxspread, x, y):
    return (
        minspread < diffcheck < maxspread and
        x['exchangeName'] != y['exchangeName'] and
        x['exchangeName'] in {'Binance', 'Kucoin', 'OKX', 'Huobi', 'MEXC Global'} and
        y['exchangeGroup'] == 'dex' and
        y['exchangeName'] != 'Raydium' and
        x['to'] in {'USDT', 'BUSD', 'USDC'} and
        y['usdVolume'] > 10000
    )


async def main():
    minspread = int(input("Input the min spread: "))
    maxspread = int(input("Input the max spread: "))
    await process_coins(minspread, maxspread, proxies)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
