import re
import asyncio
import urllib.parse
from utils import fetch_text_ensure, parse_html


class Novel:
    def __init__(self, novel_token, novel_id, base_url='https://tw.linovelib.com'):
        self.novel_token = novel_token
        self.novel_id = novel_id
        self.base_url = base_url
        self.name = ""
        self.loaded = False
        self.chapters = []


    async def load_catalog(self, session):
        url = self.get_url()
        html = await fetch_text_ensure(session, url)
        doc = parse_html(html)
        cpts = doc.findall('.//a[@class="chapter-li-a "]')
        cpt_urls = []
        for cpt in cpts:
            if cpt.attrib['href'] != 'javascript:cid(0)':
                cpt_urls.append('{}{}'.format(self.base_url, cpt.attrib['href']))

        self.chapters = chapters = [Chapter.from_url(entry) for entry in cpt_urls]
        self.loaded = True

        '''for chapter in chapters:
            await chapter.load(session)'''
        

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
        self.first_page = None

    async def load(self, session):
        html = await fetch_text_ensure(session, self.entry_url)
        doc = parse_html(html)
        js_tags = doc.findall('.//script[@type="text/javascript"]')
        
        params = self.get_params(js_tags)
        if params:
            self.first_page = first_page = ChapterPage.from_params(params)

        urls = await first_page.get_pages(session)
        
        for url in urls:
            await first_page.download_page(session, url)

    def get_params(self, jss):
        for js in jss:
            if js.text is not None and js.text.startswith('var ReadParams'):
                params = dict(re.findall(r"(\w+):'(.+?)'", js.text))
                return params
        return None

    @staticmethod
    def from_url(url):
        return Chapter(url)

class ChapterPage:
    def __init__(self, articleid, chapterid, page, url_previous, url_next, url_home) -> None:
        self.articleid = articleid
        self.chapterid = chapterid
        self.page = page
        self.url_previous = url_previous
        self.url_next = url_next
        self.url_home = url_home
        
    
    async def get_pages(self, session):
        #print('chapter_page: start get_pages:{}'.format(url))
        ref_urls = []
        url = '{}{}/{}/{}.html'.format(self.url_home, "novel", self.articleid, self.chapterid)
        ref_urls.append(url)
        for i in range(5):
            curr_url = '{}_{}.html'.format(url[:-5], i+1)
            html = await fetch_text_ensure(session, curr_url)
            doc = parse_html(html)
            ret = doc.find('.//div[@id="acontent"]/p')
            try:
                if ret.text:
                    ref_urls.append(curr_url)
            except AttributeError as e:
                pass
        return ref_urls

    async def download_page(self, session, url):
        html = await fetch_text_ensure(session, url)
        doc = parse_html(html)

        f = open("novel.txt", "a+")
        
        hs = doc.find('.//div[@class="atitle"]/h1')
        hss = doc.find('.//div[@class="atitle"]/h3')
        f.write(hs.text)
        f.write("\n")
        f.write(hss.text)
        f.write("\n")
        ps = doc.findall('.//div[@id="acontent"]/p')
        for p in ps:
            if p.text:
                f.write(p.text)
        f.write("\n")
        f.close()

    @staticmethod
    def get_url(page):
        url = '{}{}/{}/{}.html'.format(page.url_home, \
                "novel", page.articleid, page.chapterid)
        return url

    @staticmethod
    def from_params(params):
        return ChapterPage(
            params['articleid'], 
            params['chapterid'],
            params['page'], 
            params['url_previous'], 
            params['url_next'], 
            params['url_home'],)
