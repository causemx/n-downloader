import asyncio
import aiohttp

from novel import Novel



class Downloader:
    def __init__(self, session, novel_url):
        self.session = session
        self.novel = Novel.from_url(novel_url)

        self.planned_chapters = asyncio.queues.Queue()
        self.unloaded_chapters = asyncio.queues.Queue()
    
    async def get_chapt(self):
        chapter_url = await self.planned_chapters.get()
        raw  = await fetch_text_ensure(self.session, chapter_url)
        print(raw)
        self.planned_chapters.task_done()

    async def make_dive(self, url):
        raw = await fetch_text_ensure(self.session, url)
        print(raw)

        #print(doc.findall('.//div[@id="gdn"]/a').text)
        
        """
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            elif attempt < 3:
                print(f'failed #{attempt}')  # to debug, remove later
                return await make_request(session, url, attempt + 1)
        return None
        """


    async def start(self, session, cata_url):
        raw = await fetch_text_ensure(session, cata_url)
        doc = parse_html(raw)
        chapters = doc.findall('.//a[@class="chapter-li-a "]')
        for chapter in chapters:
            chapt_url = '{}{}'.format(self.base_url, chapter.attrib['href'])
            await self.planned_chapters.put(chapt_url)
        
        self.workers = workers = [asyncio.ensure_future(do_forever(self.get_chapt))]
        #workers += [asyncio.ensure_future(do_forever(self.load_chapt))]

async def download(*args, **kwargs):
    downloader = Downloader(*args, **kwargs)
    await downloader.novel.load_catalog(downloader.session)