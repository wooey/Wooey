#!/usr/bin/env python

__author__ = 'chris'
import argparse
import os
import sys
import pandas as pd
import seaborn as sns

parser = argparse.ArgumentParser(description="Create a heatmap from a delimited file.")
parser.add_argument('--tsv', help='The delimited file to plot.', type=argparse.FileType('r'), required=True)
parser.add_argument('--delimiter', help='The delimiter for fields. Default: tab', type=str, default='\t')
parser.add_argument('--row', help='The column containing row to create a heatmap from. Default to first row.', type=str)
parser.add_argument('--cols', help='The columns to choose values from (separate by a comma for multiple). Default: All non-rows', type=str)

def main():
    args = parser.parse_args()
    data = pd.read_table(args.tsv, index_col=args.row if args.row else 0, sep=args.delimiter)
    if args.cols:
        try:
            data = data.loc[:,args.cols.split(',')]
        except KeyError:
            data = data.iloc[:,[int(i)-1 for i in args.cols.split(',')]]
    if len(data.columns) > 50:
        raise BaseException('Too many columns')
    data = data[:100]
    seaborn_map = sns.clustermap(data)
    seaborn_map.savefig('{}_heatmap.png'.format(os.path.split(args.tsv.name)[1]))

if __name__ == "__main__":
    sys.exit(main())
