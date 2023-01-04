import re
import asyncio
import urllib.parse
from utils import fetch_text_ensure, parse_html


class Novel:
    def __init__(self, novel_token, novel_id, base_url='https://tw.linovelib.com'):
        self.novel_token = novel_token
        self.novel_id = novel_id
        self.base_url = base_url
        self.loaded = False


    async def load_catalog(self, session):
        url = self.get_url()
        html = await fetch_text_ensure(session, url)
        doc = parse_html(html)
        chapters = doc.findall('.//a[@class="chapter-li-a "]')
        chapter_urls = ['{}{}'.format(self.base_url, chapter.attrib['href']) for chapter in chapters]
        entry_pages = [Chapter.from_url(cu) for cu in chapter_urls]
        await entry_pages[0].load(session)
        

    def get_url(self):
        url = '{}/{}/{}/catalog'.format(
            self.base_url,
            self.novel_token,
            self.novel_id
        )
        return url
    
    @staticmethod
    def from_url(url):
        url = urllib.parse.urlparse(url)
        part = url.path.split('/')
        novel_token = part[1]
        novel_id = part[2]
        base_url = url.scheme + '://' + url.netloc
        return Novel(novel_token, novel_id, base_url)

class Chapter:
    def __init__(self, entry_url):
        self.entry_url = entry_url

    async def load(self, session):
        url = self.entry_url
        html = await fetch_text_ensure(session, url)
        doc = parse_html(html)
        js_tags = doc.findall('.//script[@type="text/javascript"]')
        for js in js_tags:
            self.get_page_params(js.text)
            

    def get_page_params(self, params_text):
        if params_text is None or not params_text.startswith('var ReadParams'):
            return
        params = dict(re.findall(r"(\w+):'(.+?)'", params_text))
        print(params['url_image'])

    @staticmethod
    def from_url(url):
        return Chapter(url)
