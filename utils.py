import asyncio
import aiohttp
import async_timeout
import html5lib
import xml.etree.ElementTree as ET
import copy

DATA_CHUNK_SIZE = 4096


def remove_namespace(root_node: ET.Element) -> ET.Element:
    '''Remove namespace from tag name of a node and its children.'''

    process_tag = lambda tag: tag.split('}')[-1]
    root_node = copy.deepcopy(root_node)
    root_node.tag = process_tag(root_node.tag)
    all_children = root_node.findall('.//*')
    for child in all_children:
        if isinstance(child.tag, str):
            child.tag = process_tag(child.tag)
    return root_node

def parse_html(html: str) -> ET.Element:
    '''Parse html and return an element tree, removing namespace.'''

    doc = html5lib.parse(html)
    doc = remove_namespace(doc)
    return doc


async def fetch_data(session, url, timeout=10.0, **kwargs):
    '''Fetch data using HTTP GET method.'''

    data = b''
    async with session.get(url, **kwargs) as r:
        with async_timeout.timeout(timeout):
            chunk = await r.content.read(DATA_CHUNK_SIZE)
        while chunk:
            with async_timeout.timeout(timeout):
                data += chunk
                chunk = await r.content.read(DATA_CHUNK_SIZE)
    return data

async def fetch_data_ensure(session, url, timeout=10.0, retry_intervial=0.5, **kwargs):
    '''Fetch data using HTTP GET method. Retry if operation failed.'''

    while True:
        try:
            data = await fetch_data(session, url, timeout, **kwargs)
        except asyncio.TimeoutError:
            pass
        except aiohttp.ClientError:
            pass
        except aiohttp.ServerDisconnectedError:
            pass
        except aiohttp.ServerConnectionError:
            pass
        else:
            break
        await asyncio.sleep(retry_intervial)
    return data

async def fetch_text(session, url, timeout=10.0, encoding=None, **kwargs):
    '''Fetch text using HTTP GET method.'''

    data = b''
    try:
        async with session.get(url, **kwargs) as r:
            with async_timeout.timeout(timeout):
                chunk = await r.content.read(DATA_CHUNK_SIZE)
            while chunk:
                with async_timeout.timeout(timeout):
                    data += chunk
                    chunk = await r.content.read(DATA_CHUNK_SIZE)
    except Exception as e:
        print("error:", str(e))
        raise ValueError('Can not read data from content')

    content_type = r.headers.get('Content-Type', '')
    if 'charset=' in content_type:
        charset = content_type.split('charset=')[-1].split(';')[0]
    else:
        charset = None
    if encoding is None:
        encoding = charset
    if encoding:
        text = data.decode(encoding)
    else:
        text = data.decode()
    return text

async def fetch_text_ensure(session, url, timeout=10.0, encoding=None, retry_intervial=0.5, **kwargs):
    '''Fetch text using HTTP GET method. Retry if operation failed.'''

    while True:
        try:
            text = await fetch_text(session, url, timeout, encoding, **kwargs)
        except asyncio.TimeoutError:
            pass
        except aiohttp.ClientError:
            pass
        except aiohttp.ServerDisconnectedError:
            pass
        except aiohttp.ServerConnectionError:
            pass
        else:
            break
        await asyncio.sleep(retry_intervial)
    return text