#!/usr/bin/env python

__author__ = 'chris'
import argparse
import os
import sys

parser = argparse.ArgumentParser(description="Create a nested heatmap from a delimited file.")
parser.add_argument('--tsv', help='The delimited file to plot.', type=argparse.FileType('r'), required=True)
parser.add_argument('--delimiter', help='The delimiter for fields. Default: tab', type=str, default='\t')
parser.add_argument('--major-index', help='The first column to group by.', type=str, required=True)
parser.add_argument('--minor-index', help='The second column to group by.', type=str, required=True)
parser.add_argument('--minor-cutoff', help='The minimum number of minor entries grouped to be considered.', type=int, default=2)
parser.add_argument('--log-normalize', help='Whether to log normalize data.', action='store_true')
parser.add_argument('--translate', help='Whether to translate data so the minimum value is zero.', action='store_true')


def main():
    args = parser.parse_args()
    import numpy as np
    import pandas as pd
    import seaborn as sns
    major_index = args.major_index
    minor_index = args.minor_index
    df = pd.read_table(args.tsv, index_col=[major_index, minor_index], sep=args.delimiter)
    df = np.log2(df) if args.log_normalize else df
    # set our undected samples to our lowest detection
    df[df==-1*np.inf] = df[df!=-1*np.inf].min().min()
    # translate our data so we have no negatives (which would screw up our addition and makes no biological sense)
    if args.translate:
        df+=abs(df.min().min())
    major_counts = df.groupby(level=[major_index]).count()
    # we only want to plot samples with multiple values in the minor index
    cutoff = args.minor_cutoff
    multi = df[df.index.get_level_values(major_index).isin(major_counts[major_counts>=cutoff].dropna().index)]

    # Let's select the most variable minor axis elements
    most_variable = multi.groupby(level=major_index).var().mean(axis=1).order(ascending=False)
    # and group by 20s
    for i in xrange(11):
        dat = multi[multi.index.get_level_values(major_index).isin(most_variable.index[10*i:10*(i+1)])]
        # we want to cluster by our major index, and then under these plot the values of our minor index
        major_dat = dat.groupby(level=major_index).sum()
        seaborn_map = sns.clustermap(major_dat, row_cluster=True, col_cluster=True)
        # now we keep this clustering, but recreate our data to fit the above clustering, with our minor
        # index below the major index (you can think of transcript levels under gene levels if you are
        # a biologist)
        merged_dat = pd.DataFrame(columns=[seaborn_map.data2d.columns])
        for major_val in seaborn_map.data2d.index:
            minor_rows = multi[multi.index.get_level_values(major_index)==major_val][seaborn_map.data2d.columns]
            major_row = major_dat.loc[major_val, ][seaborn_map.data2d.columns]
            merged_dat.append(major_row)
            merged_dat = merged_dat.append(major_row).append(minor_rows)
        merged_map = sns.clustermap(merged_dat, row_cluster=False, col_cluster=False)

        # recreate our dendrogram, this is undocumented and probably a hack but it works
        seaborn_map.dendrogram_col.plot(merged_map.ax_col_dendrogram)

        # for rows, I imagine at some point it will fail to fall within the major axis but fortunately
        # for this dataset it is not true
        seaborn_map.dendrogram_row.plot(merged_map.ax_row_dendrogram)
        merged_map.savefig('{}_heatmap_{}.png'.format(os.path.split(args.tsv.name)[1], i))

if __name__ == "__main__":
    sys.exit(main())
