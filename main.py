import asyncio
import json
import time
import aiohttp
import decimal
import sqlite3 as sl

decimal.getcontext().prec = 3

db = sl.connect('test.db')


def insertdata(coinname, xsymbol, ysymbol, xchangename, ychangename, diffcheck):
    with db:
        db.execute(f"""
					CREATE TABLE IF NOT EXISTS deals (
					xsymbol TEXT,
					ysymbol TEXT,
					xchangename TEXT,
					ychangename TEXT,
					diff int
					);
				""")
        sql = f'INSERT INTO deals (xsymbol, ysymbol, xchangename, ychangename, diff) VALUES (?, ?, ?,?,?)'
        data = [
            (xsymbol, ysymbol, xchangename, ychangename, diffcheck)
        ]
        db.executemany(sql, data)


def proxypool(amount_of_proxies):
    global proxycounter
    if proxycounter < amount_of_proxies:
        proxycounter += 1
    else:
        proxycounter = 0


proxycounter = 0


async def main():
    minspread = int(input("Input the min spread"))
    maxspread = int(input("Input the max spread"))
    amount_of_proxies= int(input("Enter the amount of proxies"))
    with open('coins.txt', 'r') as f:
        with open('proxy.txt', 'r') as p:
            coins = f.read().splitlines()
            proxies = p.read().splitlines()

            for i in range(0, len(coins)):

                url = f'https://api.cryptorank.io/v0/coins/{coins[i]}/tickers?includeQuote=false'

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, proxy=f"http://{proxies[proxycounter]}") as response:
                        proxypool(amount_of_proxies)
                        resp = await response.text()
                        jsonresp = json.loads(resp)
                        dataarray = jsonresp['data']
                        for x in dataarray:
                            for y in dataarray:
                                xprice = x['usdLast']
                                yprice = y['usdLast']
                                xspread = x.get('spread', 0)
                                yspread = y.get('spread', 0)
                                diff = abs(xprice - yprice)
                                print(x['coinName'])
                                try:
                                    percent = diff / xprice * 100
                                except ZeroDivisionError:
                                    continue
                                totalspread = xspread + yspread
                                diffcheck = percent - totalspread
                                xname = x['exchangeName']
                                yname = y['exchangeName']
                                xvolume = x['usdVolume']
                                yvolume = y['usdVolume']
                                if (diffcheck > minspread and diffcheck < maxspread) and (xname != yname) and (xname == 'Binance' or xname == 'Kucoin' or xname == 'OKX' or xname == 'Huobi' or xname == 'MEXC Global') and (y['exchangeGroup'] == 'dex') and (yname != 'Raydium') and (x['to'] == 'USDT' or x['to'] == 'BUSD' or x['to'] == 'USDC') and (yvolume > 10000):
                                    print(x['exchangeName'], x['usdLast'],
                                          y['exchangeName'], y['usdLast'], round(
                                        diffcheck, 3), y['url'])
                                    insertdata(x['coinName'],
                                               x['symbol'], y['symbol'], x['exchangeName'],
                                               y['exchangeName'],  diffcheck)


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
