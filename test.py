import asyncio
import aiohttp
from utils import *

async def call():
    sum = 0
    for i in range(10):
        await asyncio.sleep(1)
        sum += i

async def after():
    await call()
    print('call is done')

async def read(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
            doc = parse_html(html)
            foo = doc.find('.//a[@onclick="window.location.href = ReadParams.url_next;"]')
            if foo.text == "下一章":
                print('final')
            if foo.text == "下一頁":
                print('not end')
            
async def check_none_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
            doc = parse_html(html)
            foo = doc.find('.//div[@id="acontent"]/p')
            if foo.text is None:
                print('none')

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_none_page('https://tw.linovelib.com/novel/2547/92960_4.html'))

if __name__ == "__main__":
    main()
    