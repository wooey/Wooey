#!/usr/bin/env python

__author__ = 'Chris Mitchell'

# Code modified from http://stackoverflow.com/questions/20718819/downloading-images-from-google-search-using-python-gives-error

import argparse
import sys
import os
import imghdr
from urllib import FancyURLopener
import urllib2
import json

description = """
This will find you cats, and optionally, kitties.
"""

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
        searchTerm += '%20{0}'.format(args.breed)

    # Notice that the start changes for each iteration in order to request a new set of images for each loop
    found = 0
    i = 0
    downloaded = set([])
    while found <= cat_count:
        i += 1
        template = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q={}&start={}&userip=MyIP'
        url = template.format(searchTerm, i+1)
        request = urllib2.Request(url, None, {'Referer': 'testing'})
        response = urllib2.urlopen(request)

        # Get results using JSON
        results = json.load(response)
        data = results['responseData']
        dataInfo = data['results']

        # Iterate for each result and get unescaped url
        for count, myUrl in enumerate(dataInfo, 1):
            if found > cat_count:
                break
            uurl = myUrl['unescapedUrl']
            filename = uurl.split('/')[-1]
            if filename in downloaded:
                continue
            myopener.retrieve(uurl, filename)
            if imghdr.what(filename):
                found += 1
                downloaded.add(filename)
            else:
                os.remove(filename)


if __name__ == "__main__":
    sys.exit(main())
