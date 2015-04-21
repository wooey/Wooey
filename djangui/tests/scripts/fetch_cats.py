#!/usr/bin/env python

__author__ = 'Chris Mitchell'

# Code modified from http://stackoverflow.com/questions/20718819/downloading-images-from-google-search-using-python-gives-error

import argparse
import sys
from urllib import FancyURLopener
import urllib2
import json

description = """
This will find you cats.
"""

parser = argparse.ArgumentParser(description = description)
parser.add_argument('--count', help='The number of cats to find (max: 10)', type=int, default=1)
parser.add_argument('--kittens', help='Search for kittens.', action='store_true')
parser.add_argument('--breed', help='The breed of cat to find', type=str, choices=('lol', 'tabby', 'bengal', 'scottish'))


# Start FancyURLopener with defined version
class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11)Gecko/20071127     Firefox/2.0.0.11'

myopener = MyOpener()


def main():
    args = parser.parse_args()
    searchTerm = 'kittens' if args.kittens else 'cats'
    cat_count = args.count
    if args.breed:
        searchTerm += '%20{0}'.format(args.breed)

    # Notice that the start changes for each iteration in order to request a new set of     images for each loop
    for i in xrange(0, cat_count/4+1):
        template = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q={}&start={}&userip=MyIP'
        url = template.format(searchTerm, i+1)
        request = urllib2.Request(url, None, {'Referer': 'testing'})
        response = urllib2.urlopen(request)

        # Get results using JSON
        results = json.load(response)
        data = results['responseData']
        dataInfo = data['results']
        # import pdb; pdb.set_trace();

        # Iterate for each result and get unescaped url
        for count, myUrl in enumerate(dataInfo, 1):
            if count > cat_count:
                break
            my_url = myUrl['unescapedUrl']
            myopener.retrieve(myUrl['unescapedUrl'], '{0}.jpg'.format(i*4+count))


if __name__ == "__main__":
    sys.exit(main())
