# Instructions

To find information available on IMDB for a given film, enter the name of the file in the field
on the left hand side. You can also (optionally) specify a year on the optional tab.

Click "Run" to submit the query and the result will be returned under the tab "Html".

## More info

This is a demo script to show off Wooey function. The back-end of this page is a plain-old-Python command-line script
using argparse to define arguments.

    usage: IMDB.py [-h] -t TITLE [-y YEAR]

    Lookup information on films via IMDB

    optional arguments:
      -h, --help            show this help message and exit
      -t TITLE, --title TITLE
                            Title of film
      -y YEAR, --y YEAR     Year of release

The source code for this an all other demo scripts are [in the Wooey repo](https://github.com/mfitzp/Wooey/blob/master/scripts/IMDB.py).