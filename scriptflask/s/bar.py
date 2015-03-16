#!/usr/bin/env python

from collections import OrderedDict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import re
import os

import argparse
from collections import defaultdict

import utils

parser = argparse.ArgumentParser()

parser.add_argument("-m", "--metabolite", dest="metabolite", default='',
                  help="name of metabolite to plot graph for")

parser.add_argument("-f", "--file", dest="file", type=argparse.FileType('rU'), required=True,
                  help="csv file containing source data", metavar="FILE")

parser.add_argument("-b", "--batch", action="store_true", dest="batch_mode", default=False,
                  help="Batch mode (process all metabolite matches with same parameters)")

parser.add_argument("-g", "--group", dest="axisgroup", default=None,
                  help="Regular Expression pattern for axis cluster")

parser.add_argument("--multiplot", action="store_true", dest="multiplot", default=False,
                  help="Plot more than one graph per figure")

parser.add_argument("--shareyaxis", action="store_true", dest="shareyaxis", default=False,
                  help="Share y axis scale")

parser.add_argument("-s", "--search", dest="search", default=None,
                  help="Show classes matching this regex")

parser.add_argument("-t", dest="tests", default=None,
                  help="CLASS,CLASS combinations to statisically test (space-separated)")

parser.add_argument("--statistic", dest="statistic", default=None, choices={'tind':'Independent-samples T-test', 'trel':'Related-samples T-test'},
                  help="Statistical test: tind (t-independent), trel (t-related)")

parser.add_argument("--xlabel", dest="xlabel", default='',
                  help="X axis label")

parser.add_argument("--ylabel", dest="ylabel", default='',
                  help="Y axis label")

parser.add_argument("--ylim", dest="ylim", default=None, type=float,
                  help="min,max for y axis")

parser.add_argument("--title", dest="title", default=None,
                  help="Graph title")

parser.add_argument("--dpi", dest="dpi", default=72, type=int,
                  help="DPI of output (TIF format only)")

parser.add_argument("--format", dest="format", default='png',
                  help="File format for output")

parser.add_argument("--annotate", action="store_true", dest="annotate", default=False,
                  help="show command annotation for generation")

args = parser.parse_args()

colors = ['#348ABD', '#7A68A6', '#A60628', '#467821', '#CF4457', '#188487', '#E24A33', 'r', 'b', 'g', 'c', 'm', 'y', 'k', 'w']

# Extract file root from the edge file name
filebase = os.path.splitext(args.file.name)[0]
[null, sep, string] = filebase.partition('-')
filesuff = sep + string
nodes = OrderedDict()

(metabolites, allquants, globalylim) = utils.read_metabolite_datafile(args.file, args)

# Turn off interactive plotting, speed up
plt.ioff()
figures = list()
multiax = None
ymaxf = 0

for metabolite in metabolites[:]:
    print("Processing %s" % metabolite)
    quants = allquants[metabolite]

    if args.search:
        okeys = quants.keys()
        for label in quants.keys():
            match = re.search(args.search, label)
            if not match:
                del quants[label]
        print("Filter matching classes '%s' with '%s' gives '%s'" % (', '.join(okeys), args.search, ', '.join(quants.keys())))
        if len(quants.keys()) == 0:
            print("Nothing left!; deleting metabolite")
            metabolites.remove(metabolite)
            continue

    # Apply regex to split axis groups if specified
    if args.axisgroup:

        axisgroups = defaultdict(list)
        for label in quants.keys():
            match = re.search(args.axisgroup, label)
            if match:
                axisgroups[match.group(1)].append(label)
            #else:
            #    axisgroups['non-matched'].append(label)
        if len(axisgroups) == 0:
            print("No matching classes found for axisgroup regex, try again")
            exit()
        print("Axis groupings completed: " + ", ".join(axisgroups))

    else:
        # No groups, create dummy for 'all'
        axisgroups = {'not-grouped': quants.keys()}

    ind = list()
    graph = {
        'ticks': list(),
        'means': list(),
        'stddev': list(),
        'colors': list(),
        'ylim': (0, 0),
    }

    # Sort the axis groups so follow some sort of logical order
    axisgroupsk = axisgroups.keys()
    axisgroupsk.sort()
    ymin = 0
    ymax = 0
    for counter, axisgroup in enumerate(axisgroupsk):
        l = axisgroups[axisgroup]
        l.sort()
        graph['ticks'] = graph['ticks'] + l
        for key in l:
            graph['means'].append(np.mean(quants[key]))
            graph['stddev'].append(np.std(quants[key]))
            ymax = max(ymax, max(quants[key]))
            ymin = min(ymin, min(quants[key]))
        ind = ind + list(np.arange(1 + counter + len(ind), 1 + counter + len(ind) + len(l)))
        graph['colors'] = graph['colors'] + colors[0: len(l)]

    num = len(ind)
    width = 0.8  # the width of the bars: can also be len(x) sequence
    if args.shareyaxis:
        graph['ylim'] = globalylim
    else:
        graph['ylim'] = (ymin, ymax)

    # Split error pos+neg to give single up/down errorbar in correct direction
    yperr = [(1, 0)[x > 0] for x in graph['means']]
    ynerr = [(1, 0)[x < 0] for x in graph['means']]
    yperr = np.array(list(yperr)) * np.array(list(graph['stddev']))
    ynerr = np.array(list(ynerr)) * np.array(list(graph['stddev']))

    if args.multiplot:
        # Keep using same figure, append subplots
        if not multiax:
            #adjustprops = dict(left=0.1, bottom=0.1, right=0.97, top=0.93, wspace=0.2, hspace=0.2)
            fig = plt.figure()
            multiax = fig.add_subplot(1, len(metabolites), 1)
            figures.append(multiax)
        else:
            if not args.shareyaxis:
                fp = fig.add_subplot(1, len(metabolites), len(figures) + 1, sharey=multiax)
                plt.setp(fp.get_yticklabels(), visible=False)
                plt.setp(fp.get_yaxis(), visible=False)
            else:
                fp = fig.add_subplot(1, len(metabolites), len(figures) + 1)

            figures.append(fp)
    else:
        # New figure
        figures.append(plt.figure())

    plt.bar(ind, graph['means'], width, label=graph['ticks'], color=graph['colors'], ecolor='black', align='center', yerr=[yperr, ynerr])

    plt.xticks(ind, graph['ticks']) #, rotation=45)

    if args.title:
        plt.title(args.title)
    else:
        plt.title(metabolite)

    plt.gca().xaxis.set_label_text(args.xlabel)
    plt.gca().yaxis.set_label_text(args.ylabel)

    # Add some padding either side of graphs
    plt.xlim(ind[0] - 1, ind[-1] + 1)

    if args.annotate:
        utils.annotate_plot(plt, options)

    fig = plt.gcf()
    # Horizontal axis through zero
    plt.axhline(0, color='k')

    if args.multiplot:  # Scale the multiplots a bit more reasonably
        fig.set_size_inches(5 + len(metabolites) * 3, 6)
    else:
        fig.set_size_inches(8, 6)

    # Get ylimits for significance bars
    ymin, ymax = graph['ylim']

    sigs = list()
    if args.tests:
        from scipy import stats
        tests = args.tests.split()

        for test in tests:
            classt = test.split(',')
            if args.statistic == 'trel':
                t, p = stats.ttest_rel(quants[classt[0]], quants[classt[1]])
            else:
                t, p = stats.ttest_ind(quants[classt[0]], quants[classt[1]])

            # sigs.append( { a:classt[0], b:classt[1], p:p } )
            # We now lave a list of significant comparisons in significant
            bxstart = ind[graph['ticks'].index(classt[0])]
            bxend = ind[graph['ticks'].index(classt[1])]

            # Nudge up to prevent overlapping
            ymax = ymax + ((ymax - ymin) * 0.1)

            # Plot the bar on the graph
            c = patches.FancyArrowPatch(
                    (bxstart, ymax),
                    (bxend, ymax),
                    arrowstyle="|-|", lw=2)
            ax = plt.gca()

            plt.text(bxstart + (bxend - float(bxstart)) / 2, ymax + (ymax * 0.01), utils.sigstars(p), size=16, ha='center', va='bottom')
            ax.add_patch(c)
            print("Stats (%s): %s vs %s; p=%s" % (args.statistic, classt[0], classt[1], p))

        # Final nudge up over last bar
        ymax = ymax + ((ymax - ymin) * 0.1)

    # Store final limit
    ymaxf = max(ymaxf, ymax)

    if args.ylim:
        ylim = args.ylim.split(',')
        plt.ylim(int(ylim[0]), int(ylim[1]))

    if not args.multiplot:
        # Adjust plot on multiplot
        plt.ylim(ymin, ymaxf)
        ymaxf = 0
        print("Save as 'bar%s-%s.%s'" % (filesuff, metabolite, args.format))
        plt.savefig('bar%s-%s.%s' % (filesuff, metabolite, args.format), dpi=args.dpi, transparent=False)

if args.multiplot:
    # Adjust plot on multiplot
    plt.ylim(ymin, ymaxf)
    print("Save as 'bar%s-%s.%s'" % (filesuff, '-'.join(metabolites), args.format))
    plt.savefig('bar%s-%s.%s' % (filesuff, '-'.join(metabolites), args.format), dpi=args.dpi, transparent=False)

plt.close()
