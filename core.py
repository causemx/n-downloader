import asyncio
import aiohttp
import logging
import traceback
logger = logging.getLogger('n-downloader')

from novel import Novel


async def do_forever(job):
    while True:
        try:
            await job()
        except asyncio.CancelledError:
            break
        except:
            logger.error(traceback.format_exc())

class Downloader:
    def __init__(self, session, novel_url):
        self.session = session
        self.novel = Novel.from_url(novel_url)

        self.queue1 = asyncio.queues.Queue()
        self.queue2 = asyncio.queues.Queue()
    
    async def get_chapt(self):
        chapter = await self.queue1.get()
        for id in range(chapter.page_count):
            page = await chapter.get_page(self.session, id)
        await self.queue2.put(page)
        self.queue1.task_done()

    async def load_page(self):
        page = await self.queue2.get()
        print(page.chapterid)
        self.queue2.task_done()

    async def start(self):
        if not self.novel.loaded:
            await self.novel.load_catalog(self.session)
        
        for chapter in self.novel.chapters:
            await self.queue1.put(chapter)
        
        self.workers = workers = [asyncio.ensure_future(do_forever(self.get_chapt))]
        workers += [asyncio.ensure_future(do_forever(self.load_page))]

    async def join(self):
        await self.queue1.join()
        await self.queue2.join()
        #while self.unloaded_pages.qsize() != 0 or self.unloaded_pages._unfinished_tasks != 0:
         #   await self.unloaded_pages.join()

async def download(*args, **kwargs):
    downloader = Downloader(*args, **kwargs)
    await downloader.start()
    await downloader.join()
    #await downloader.novel.load_catalog(downloader.session)