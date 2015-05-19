#!/usr/bin/env python
import pandas as pd
import numpy as np
import scipy as sp
from scipy import stats

import matplotlib.pyplot as plt
import re
import os
import string
import requests

import logging

import argparse


IDENTIFIERS = {
    # GN   Name=LTA4H; Synonyms=LTA4;
    'Gene Name': re.compile('^GN\s+Name=(.*?)\W', re.MULTILINE),
    # DR   BioGrid; 110226; 12.
    'BioGrid': re.compile('^DR\s+BioGrid; (\w*?);', re.MULTILINE),
    # DR   IntAct; P09960; 5.
    'IntAct': re.compile('^DR\s+IntAct; (\w*?);', re.MULTILINE),
    # DR   STRING; 9606.ENSP00000228740; -.
    'STRING': re.compile('^DR\s+STRING; (\w*?);', re.MULTILINE),
    # DR   ChEMBL; CHEMBL4618; -.
    'ChEMBL': re.compile('^DR\s+PhosphoSite; (\w*?);', re.MULTILINE),
    # DR   PhosphoSite; P09960; -.
    'PhosphoSite': re.compile('^DR\s+PhosphoSite; (\w*?);', re.MULTILINE),
    # DR   GeneCards; GC12M096394; -.
    'GeneCards': re.compile('^DR\s+GeneCards; (\w*?);', re.MULTILINE),
    # DR   BioCyc; MetaCyc:HS03372-MONOMER; -.
    'BioCyc': re.compile('^DR\s+BioCyc; (\w*?);', re.MULTILINE),
}


parser = argparse.ArgumentParser(description='Map Uniprot IDs to gene identifiers.')

parser.add_argument("-f", "--file", dest="file", type=argparse.FileType('rU'), required=True,
                  help="Excel or CSV file containing at least one column of UniProt IDs", metavar="FILE")

parser.add_argument("-c", "--column", dest="column", default='A', type=str,
                  help="Column header name, or label (A, B, C, D, E.. AA, AB, AC, AD, AE) to map IDs from")

parser.add_argument("--has_header", dest="has_header", default=False, action="store_true",
                  help="Does the source file have a header row?")

parser.add_argument("--identifier", dest="identifier", default='Gene Name', choices=['Gene Name', 'BioGrid', 'IntAct', 'STRING', 'ChEMBL', 'PhosphoSite', 'GeneCards', 'BioCyc'], type=str,
                  help="Target identifier format")

args = parser.parse_args()


if __name__ == "__main__":

    basename = os.path.basename(args.file.name)
    extension = os.path.splitext(basename)[1] # .csv or .xlsx

    if args.has_header:
        header = 0
    else:
        header = None

    if extension == '.csv':
        print("Opening file %s as CSV" % basename)
        df = pd.read_csv(args.file, delimiter=',', skiprows=None, low_memory=False, header=header)

    elif extension == '.txt':
        print("Opening file %s as TXT" % basename)
        df = pd.read_csv(args.file, delimiter='\t', skiprows=None, low_memory=False, header=header)

    else:
        print("Opening file %s as Excel format" % basename)
        df = pd.read_excel(args.file, header=header)

    # We should now have a dataframe containning the IDs
    if args.has_header:
        source_ids = df[args.column].values

    else:
        def col2num(col):
            num = 0
            for c in col:
                if c in string.ascii_letters:
                    num = num * 26 + (ord(c.upper()) - ord('A')) + 1
            return num

        # Work out the index, using Excel style numbering
        idx = col2num(args.column) - 1
        source_ids = df.iloc[:, idx].values

    # Build mapping (using dict) to speed up duplicates

    mapping = {}
    source_ids = set( list(source_ids) )

    rx = re.compile(IDENTIFIERS[args.identifier])

    for identifier in source_ids:

        url = 'http://www.uniprot.org/uniprot/%s.txt' % str(identifier)

        result = requests.get(url)
        findgene = rx.search(result.text)
        if findgene:
            target = str(findgene.group(1))
            mapping[identifier] = target
            print("Mapping %s to %s" % (identifier, target))

        else:
            print("NO MATCH FOUND for %s" % identifier)


    # The mapping is complete
    df[args.identifier] = [mapping[i] if i in mapping else '' for i in source_ids ]

    print("Writing output")

    if extension == '.csv':
        df = df.to_csv(basename, sep=',', index=False)

    elif extension == '.txt':
        df = df.to_csv(basename, sep='\t', index=False)

    else:
        df = df.to_excel(basename, index=False)

