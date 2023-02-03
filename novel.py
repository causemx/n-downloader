import re
import os
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

        def convert(list):
            return tuple(i for i in list)

        url = self.get_url()
        html = await fetch_text_ensure(session, url)
        doc = parse_html(html)

        header = ''
        entries = []
        page_count = 0

        di = doc.iter('li')
        while True:
            try:
                d = di.__next__()
                a = d.find('.//a[@class="chapter-li-a "]')
                if a.attrib['href'] != 'javascript:cid(0)':
                    entries.append('{}{}'.format(self.base_url, a.attrib['href']))
                page_count = page_count + 1
            except AttributeError:
                if len(entries) != 0:
                    self.chapters.append(Chapter(header, convert(entries), page_count)) 
                    entries.clear()
                    page_count = 0
                header = d.text
            except StopIteration:
                pass # reach the end of iterator
                self.chapters.append(Chapter(header, convert(entries), page_count)) 
                break

        self.loaded = True 

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
    def __init__(self, name, entry_urls, page_count):
        self.name = name
        self.entry_urls = entry_urls
        self.page_count = page_count

    async def get_page(self, session, page_id):
        try:
            html = await fetch_text_ensure(session, self.entry_urls[page_id])
            doc = parse_html(html)
            js_tags = doc.findall('.//script[@type="text/javascript"]')
            
            params = self.get_params(js_tags)
            if params:
                return ChapterPage.from_params(params)
        except IndexError:
            print('entry_url_length:{}, error index:{}'.format(len(self.entry_urls), page_id))

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
        self.loaded = False
        self.ref_urls = []
        
    async def load(self, session):
        #print('chapter_page: start get_pages:{}'.format(url))
        url = '{}{}/{}/{}.html'.format(self.url_home, "novel", self.articleid, self.chapterid)
        for i in range(5):
            curr_url = '{}_{}.html'.format(url[:-5], i+1)
            html = await fetch_text_ensure(session, curr_url)
            doc = parse_html(html)
            ret = doc.find('.//div[@id="acontent"]/p')
            try:
                if ret.text:
                    self.ref_urls.append(curr_url)
            except AttributeError as e:
                pass
        self.loaded = True

    async def download_page(self, session, mode, dest):
        for url in self.ref_urls:
            html = await fetch_text_ensure(session, url)
            doc = parse_html(html)
            if not os.path.isdir(dest):
                os.makedirs(dest)
            
            if mode is 'integrated':
                f = open("{}/{}.txt".format(dest, 'content'), "a+")
            elif mode is 'seperated':
                f = open("{}/{}.txt".format(dest, self.chapterid), "a+")
            
            hs = doc.find('.//div[@class="atitle"]/h1')
            f.write(hs.text)
            f.write("\n\n")
            ps = doc.findall('.//div[@id="acontent"]/p')
            for p in ps:
                if p.text:
                    f.write(p.text)
            f.write("\n\n")
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
