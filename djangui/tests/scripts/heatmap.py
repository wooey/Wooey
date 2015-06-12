#!/usr/bin/env python

__author__ = 'chris'
import argparse
import os
import sys
import pandas as pd
import seaborn as sns
import numpy as np

parser = argparse.ArgumentParser(description="Create a heatmap from a delimited file.")
parser.add_argument('--tsv', help='The delimited file to plot.', type=argparse.FileType('r'), required=True)
parser.add_argument('--delimiter', help='The delimiter for fields. Default: tab', type=str, default='\t')
parser.add_argument('--row', help='The column containing row to create a heatmap from. Default to first row.', type=str)
parser.add_argument('--cols', help='The columns to choose values from (separate by a comma for multiple). Default: All non-rows', type=str)
parser.add_argument('--log-normalize', help='Whether to log normalize data.', action='store_true')

def main():
    args = parser.parse_args()
    data = pd.read_table(args.tsv, index_col=args.row if args.row else 0, sep=args.delimiter, encoding='utf-8')
    if args.cols:
        try:
            data = data.loc[:,args.cols.split(',')]
        except KeyError:
            data = data.iloc[:,[int(i)-1 for i in args.cols.split(',')]]
    if len(data.columns) > 50:
        raise BaseException('Too many columns')
    data = np.log2(data) if args.log_normalize else data
    data[data==-1*np.inf] = data[data!=-1*np.inf].min().min()
    width = 5+0 if len(data.columns)<50 else (len(data.columns)-50)/100
    row_cutoff = 1000
    height = 15+0 if len(data)<row_cutoff else (len(data)-row_cutoff)/75.0
    seaborn_map = sns.clustermap(data, figsize=(width, height))
    seaborn_map.savefig('{}_heatmap.png'.format(os.path.split(args.tsv.name)[1]))
    seaborn_map.data2d.to_csv('{}_heatmap.tsv'.format(os.path.split(args.tsv.name)[1]), sep='\t')

if __name__ == "__main__":
    sys.exit(main())
