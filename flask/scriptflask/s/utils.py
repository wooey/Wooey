import re,os
import csv
from collections import defaultdict
import math

def sigstars(p):
    # Return appropriate number of stars or ns for significance

    if (p<=0.0001):
        s = '****'
    elif (p<=0.001):
        s = '***'
    elif (p<=0.01):
        s = '**'
    elif (p<=0.05):
        s = '*'
    else:
        s = 'ns'
    return s


def read_metabolite_datafile( fp, options ):
    
    # Read in data for the graphing metabolite, with associated value (generate mean)
    reader = csv.reader( fp, delimiter=',', dialect='excel')
    # Find matching metabolite column
    hrow = reader.next()
    try:
        metabolite_column = hrow.index( options.metabolite )
        print("'%s' found" % (options.metabolite))
        metabolites = [ options.metabolite ]
    except:
        all_metabolites = hrow[2:]
        metabolites = filter(lambda x:re.match('(.*)' + options.metabolite + '(.*)', x), all_metabolites)
        if len(metabolites) ==0:
            print("Metabolite not found, try again. Pick from one of:")
            print(', '.join( sorted(all_metabolites) )  )
            exit()
        elif len(metabolites) > 1:
            print("Searched '%s' and found multiple matches:" % (options.metabolite))
            print(', '.join( sorted(metabolites) ))
            if not options.batch_mode:
                print("To process all the above together use batch mode -b")
                exit()
        elif len(metabolites) ==1:
            print("Searched '%s' and found match in '%s'" % (options.metabolite, metabolites[0]))
    
    
    # Build quants table for metabolite classes
    allquants = dict()
    for metabolite in metabolites:
        allquants[ metabolite ] = defaultdict(list)
    
    ymin = 0
    ymax = 0
    
    for row in reader:
        if row[1] != '.': # Skip excluded classes # row[1] = Class
            for metabolite in metabolites:
                metabolite_column = hrow.index( metabolite )   
                if row[ metabolite_column ]:
                    allquants[metabolite][ row[1] ].append( float(row[ metabolite_column ]) )
                    ymin = min( ymin, float(row[ metabolite_column ]) )
                    ymax = max( ymax, float(row[ metabolite_column ]) )
                else:
                    allquants[metabolite][ row[1] ].append( 0 )
        
    return ( metabolites, allquants, (ymin,ymax) )
    
def annotate_plot(plt, options):
    annod = vars(options)
    annol = ', \n'.join(["%s=%s" % (x, annod[x]) for x in annod.keys()])
    bbox = dict( facecolor='#eeeeff', alpha=1, edgecolor='#000000',boxstyle="Square,pad=1")
    plt.text(1.1, 1.1, annol,
        backgroundcolor='#eeeeff',
        fontsize='x-small',
        ha='right',
        va='top',
        bbox=bbox,
        transform = plt.gca().transAxes)

import numpy

def smooth(x,window_len=11,window='hanning'):
 
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    s=numpy.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=numpy.ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')

    y=numpy.convolve(w/w.sum(),s,mode='valid')
    return y