import asyncio
import json
import aiohttp
import decimal

decimal.getcontext().prec = 3

apikey = ""

url = f'https://api.cryptorank.io/v1/currencies?limit=5000&api_key={apikey}'


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            resp = await response.text()
            jsonresp = json.loads(resp)
            dataarray = jsonresp['data']
            with open('coins.txt', 'a') as f:
                for item in dataarray:
                    f.write(item['slug'] + '\n')


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
