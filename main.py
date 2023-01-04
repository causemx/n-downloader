import re
import os
import sys
import logging
import asyncio
import aiohttp
import argparse
from http.cookies import SimpleCookie

logger = logging.getLogger("n-downloader")
import core


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookie-storage', type=str, default='./cookies.dat', dest='cookie_file_path',
                        help='path of the text file that stores cookies')

    subparsers = parser.add_subparsers(title='command', dest='command_name')
 

    parser_download = subparsers.add_parser('download', help='download images from a gallery')
    parser_download.add_argument('novel_url', type=str, help='Url of the novel that you want to download')
    parser_download.add_argument('--download-timeout', type=float, dest='download_timeout', default=5.0, \
        help='Timeout of download connections')
    parser_download.set_defaults(func=do_download)

    parser_cookie_export = subparsers.add_parser('cookie-export', help='export cookies to stdout')
    parser_cookie_export.set_defaults(func=do_cookie_export)

    parser_cookie_update = subparsers.add_parser('cookie-update', help='import and update cookies from stdin')
    parser_cookie_update.set_defaults(func=do_cookie_update)

    args = parser.parse_args(args)
    if not args.command_name:
        parser.print_help()
        return 1
    if not args.novel_url:
        parser.print_help()
        return 1

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        async with aiohttp.ClientSession(loop=loop) as session:
            args.session = session
            prepare_cookies(args)
            await args.func(args)


    loop.run_until_complete(run())
    save_cookies(args)
    return 0

async def do_download(args):
    #await core.load_preview(args.session, args.catalog_url)
    await core.download(args.session, args.novel_url)

def prepare_cookies(args):
    path = args.cookie_file_path
    if os.path.exists(path):
        args.session.cookie_jar.load(path)

def save_cookies(args):
    args.session.cookie_jar.save(args.cookie_file_path)

async def do_cookie_export(args):
    for cookie in args.session.cookie_jar:
        print(cookie.output())


async def do_cookie_update(args):
    cookie = SimpleCookie()
    for line in sys.stdin:
        if line.strip():
            cookie.load(line.split('Set-Cookie: ')[1])
            args.session.cookie_jar.update_cookies(cookie)

def setup_logger(logger):
    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter('%(asctime)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)
    logger.info('stream logger added')

if __name__ == '__main__':
    from sys import argv, exit
    setup_logger(logger)
    error_code = main(argv[1:])
    if error_code != 0:
        exit(error_code)