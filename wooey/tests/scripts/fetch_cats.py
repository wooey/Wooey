#!/usr/bin/env python

__author__ = 'Chris Mitchell'

import argparse
import os
import socket
import sys
from urllib import FancyURLopener
from apiclient import discovery

description = """
This will find you cats, and optionally, kitties.
"""

socket.setdefaulttimeout(10)

parser = argparse.ArgumentParser(description = description)
parser.add_argument('--count', help='The number of cats to find (max: 10)', type=int, default=1)
parser.add_argument('--kittens', help='Search for kittens.', action='store_true')
parser.add_argument('--breed', help='The breed of cat to find', type=str, choices=('lol', 'tabby', 'bengal', 'scottish', 'grumpy'))

# Start FancyURLopener with defined version
class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127     Firefox/2.0.0.11'

myopener = MyOpener()

def main():
    args = parser.parse_args()
    searchTerm = 'kittens' if args.kittens else 'cats'
    cat_count = args.count if args.count < 10 else 10
    if args.breed:
        searchTerm += ' {0}'.format(args.breed)

    # Notice that the start changes for each iteration in order to request a new set of images for each loop
    service = discovery.build('customsearch', 'v1', developerKey=os.environ.get('GOOGLE_DEV_KEY'))
    cse = service.cse()
    search_kwrds = {
        'q': searchTerm,
        'cx': os.environ.get('GOOGLE_CX'),
        'fileType': 'jpg',
        'imgType': 'photo',
        'num': cat_count,
        'searchType': 'image'
    }
    request = cse.list(**search_kwrds)
    response = request.execute()
    for item in response.get('items', []):
        url = item.get('link')
        filename = url.split('/')[-1]
        try:
            myopener.retrieve(url, filename)
        except IOError:
            continue


if __name__ == "__main__":
    sys.exit(main())
