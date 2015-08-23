# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 01:38:57 2015

@author: cliffk
"""

import add_optima_paths # analysis:ignore
from utils import tic, toc, printdata as pd # analysis:ignore
from dataio import loaddata
from pylab import figure, subplot, arange, maximum, savefig
from portfolio import loadportfolio


from matplotlib.pyplot import rc 
rc('font', family='serif') 
rc('font', serif='Linux Biolinum') 
rc('font', size=14)

dosave = True
makeslide1 = False
makeslide2 = True
makeslide3 = False
makeslide4 = False

nationaljson = '/u/cliffk/unsw/countries/malawi/malawi-steeper-ccocs.json'
portfolioname = '/u/cliffk/unsw/optima/server/src/sim/tests/malawi-gpa-done.npz'
districtstouse = ['Blantyre City', 'Chitipa']



##################################################################
## Allocation plots
##################################################################

def plotallocations(progdata, progs, labels, factor=1e6, compare=True):
    ''' Instead of stupid pie charts, make some nice bar charts '''
    nprogs = len(progs)
    
    fig = figure(figsize=(10,6))
    fig.subplots_adjust(left=0.10) # Less space on left
    fig.subplots_adjust(right=0.98) # Less space on right
    fig.subplots_adjust(bottom=0.30) # Less space on bottom
    fig.subplots_adjust(wspace=0.30) # More space between
    fig.subplots_adjust(hspace=0.40) # More space between
    
    from gridcolormap import gridcolormap
    colors = gridcolormap(nprogs)
    
    ax = []
    xbardata = arange(nprogs)+0.5
    ymax = 0
    for plt in range(len(progdata)):
        ax.append(subplot(len(progdata),1,plt+1))
        ax[-1].hold(True)
        for p in range(nprogs):
            ax[-1].bar([xbardata[p]], [progdata[plt][p]/factor], color=colors[p], linewidth=0)
            if plt==1 and compare:
                ax[-1].bar([xbardata[p]], [progdata[0][p]/factor], color='None', linewidth=1)
        ax[-1].set_xticks(arange(nprogs)+1)
        if plt==0: ax[-1].set_xticklabels('')
        if plt==1: ax[-1].set_xticklabels(progs,rotation=90)
        ax[-1].set_xlim(0,nprogs+1)
        
        if factor==1: ax[-1].set_ylabel('Spending (US$)')
        elif factor==1e3: ax[-1].set_ylabel("Spending (US$'000s)")
        elif factor==1e6: ax[-1].set_ylabel('Spending (US$m)')
        ax[-1].set_title(labels[plt])
        ymax = maximum(ymax, ax[-1].get_ylim()[1])
    for plt in range(len(progdata)):
        if compare: ax[plt].set_ylim((0,ymax))




##################################################################
## Load portfolio
##################################################################
if 'P' not in locals().keys():
    print('Loading portfolio...')
    t = tic()
    P = loadportfolio(portfolioname)
    toc(t)


##################################################################
## Slide 1 -- national pie chart
##################################################################

if 'D' not in locals().keys(): D = loaddata(nationaljson)
allocs = D['optimizations'][-1]['result']['plot'][0]['alloc']
progs = allocs[0]['legend']
origalloc = allocs[0]['piedata']
optimalloc = allocs[1]['piedata']
progdata = [origalloc,optimalloc]
labels = ['Current budget allocation','Optimal budget allocation']
if makeslide1:
    plotallocations(progdata, progs, labels)
    if dosave: savefig('/u/cliffk/unsw/countries/malawi/results/nationalallocation.png',dpi=200)



##################################################################
## Slide 2 -- map of Malawi colored by PLHIV
##################################################################





##################################################################
## Slide 3 -- map of Malawi colored by spend
##################################################################





##################################################################
## Slide 4 -- allocations from two different regions
##################################################################

progdata = [0, 0]
for i in range(len(P.gpalist[0])):
    for dist in range(2):
        if P.gpalist[0][i].getregion().getregionname()==districtstouse[dist]:
            progdata[dist] = P.gpalist[0][i].simlist[2].alloc
if makeslide4:
    plotallocations(progdata, progs, districtstouse, factor=1e3, compare=False)
    if dosave: savefig('/u/cliffk/unsw/countries/malawi/results/districtallocation.png',dpi=200)


print('Done.')