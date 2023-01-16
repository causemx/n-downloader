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
    def convert(list):
        return tuple(i for i in list)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
            doc = parse_html(html)
            content = {}
            urls = []
            for d in doc.iter('li'):
                if d.text:
                    if len(urls) != 0:
                        content.update({d.text: convert(urls)})
                        urls.clear()
                else:
                    a = d.find('.//a[@class="chapter-li-a "]')
                    urls.append(a.attrib['href'])
            print(content)
            
async def check_none_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            html = await r.text()
            doc = parse_html(html)
            foo = doc.find('.//div[@id="acontent"]/p')
            if not foo.text:
                print('none')

async def write_content(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            f = open("foo.txt", "a+")
            html = await r.text()
            doc = parse_html(html)
            hs = doc.find('.//div[@class="atitle"]/h1')
            hss = doc.find('.//div[@class="atitle"]/h3')
            f.write(hs.text)
            f.write(hss.text)
            ps = doc.findall('.//div[@id="acontent"]/p')
            [f.write(p.text) for p in ps]
            f.write("\n")
            f.close()



def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(read('https://tw.linovelib.com/novel/2547/catalog'))

if __name__ == "__main__":
    main()
    