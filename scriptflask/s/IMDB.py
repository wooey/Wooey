#!/usr/bin/env python

import argparse
import json
import requests

parser = argparse.ArgumentParser(description="Lookup information on films via IMDB")

parser.add_argument("-t", "--title", dest="title", required=True, type=str,
                  help="Title of film")

parser.add_argument("-y", "--y", dest="year", required=False, type=int,
                  help="Year of release")

args = parser.parse_args()

title = args.title
title = title.replace(' ', '+')

#The actual query
url = "http://www.imdbapi.com/?t=" + title
if args.year:
    url += "&y=%d"  % year

r = requests.get(url)
if r.status_code == 200:
    print("Successfully retreived data from %s" % url)

    data = json.loads(r.text)
    
    # Add some nice features to the output
    if 'Poster' in data:
        data['Poster'] = '<a href="%s">View</a>' % data['Poster']
    
    if 'imdbID' in data:
        data['imdbID'] = '<a href="http://www.imdb.com/title/%s/">View on IMDB</a>' % data['imdbID']
    
    table = ""
    for k, v in data.items():
        table += "<tr><th>%s</th><td>%s</td></tr>" % (k, v)

    with open('Result.html', 'w') as f:
        f.write("""<html><body><table>%s</table></body></html>""" % table)

else:
    print("Something went wrong: Error code %d" % r.status_code)