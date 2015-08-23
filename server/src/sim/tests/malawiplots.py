# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 01:38:57 2015

@author: cliffk
"""

import add_optima_paths # analysis:ignore
from utils import printdata as pd
from dataio import loaddata
from pylab import figure, subplot, arange, maximum, savefig

from matplotlib.pyplot import rc 
rc('font', family='serif') 
rc('font', serif='Linux Biolinum') 
rc('font', size=14)

dosave = True
makeslide1 = True
makeslide2 = True
makeslide3 = False
makeslide4 = False

##################################################################
## Slide 1 -- national pie chart
##################################################################

if makeslide1:
    
    traditional = False
    
    nationaljson = '/u/cliffk/unsw/countries/malawi/malawi-steeper-ccocs.json'
    D = loaddata(nationaljson)
    if traditional:
        from viewresults import viewoptimresults
        viewoptimresults(D['optimizations'][-1]['result']['plot'][0])
    else:
        allocs = D['optimizations'][-1]['result']['plot'][0]['alloc']
        progs = allocs[0]['legend']
        origalloc = allocs[0]['piedata']
        optimalloc = allocs[1]['piedata']
        progdata = [origalloc,optimalloc]
        nprogs = len(progs)
        
        fig = figure(figsize=(10,6))
        fig.subplots_adjust(left=0.05) # Less space on left
        fig.subplots_adjust(right=0.98) # Less space on right
        fig.subplots_adjust(bottom=0.30) # Less space on bottom
        fig.subplots_adjust(wspace=0.30) # More space between
        fig.subplots_adjust(hspace=0.40) # More space between
        
        from gridcolormap import gridcolormap
        colors = gridcolormap(nprogs)
        
        labels = ['Current budget allocation','Optimal budget allocation']
        ax = []
        xbardata = arange(nprogs)+0.5
        factor = 1e6
        ymax = 0
        for plt in range(len(progdata)):
            ax.append(subplot(len(progdata),1,plt+1))
            ax[-1].hold(True)
            for p in range(nprogs):
                ax[-1].bar([xbardata[p]], [progdata[plt][p]/factor], color=colors[p], linewidth=0)
                if plt==1:
                    ax[-1].bar([xbardata[p]], [progdata[0][p]/factor], color='None', linewidth=1)
            ax[-1].set_xticks(arange(nprogs)+1)
            if plt==0: ax[-1].set_xticklabels('')
            if plt==1: ax[-1].set_xticklabels(progs,rotation=90)
            ax[-1].set_xlim(0,nprogs+1)
            ax[-1].set_ylabel('Spending (US$m)')
            ax[-1].set_title(labels[plt])
            ymax = maximum(0, ax[-1].get_ylim()[1])
        for plt in range(len(progdata)):
            ax[plt].set_ylim((0,ymax))
    
    if dosave:
        savefig('/u/cliffk/unsw/countries/malawi/results/nationalallocation.png',dpi=200)


##################################################################
## Slide 2 -- map of Malawi colored by PLHIV
##################################################################

print('Done.')