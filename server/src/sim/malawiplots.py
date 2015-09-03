# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 01:38:57 2015

@author: cliffk
"""

import add_optima_paths # analysis:ignore
from utils import tic, toc, printdata as pd, findinds # analysis:ignore
from dataio import loaddata
from pylab import figure, subplot, arange, maximum, savefig, zeros, array
from portfolio import loadportfolio
from colortools import vectocolor


from matplotlib.pyplot import rc 
rc('font', family='serif') 
rc('font', serif='Linux Biolinum') 
rc('font', size=14)

dosave = 1
makeslide1 = 1
makeslide2 = 1
makeslide3 = 1
makeslide4 = 1

nationaljson = '/u/cliffk/unsw/countries/malawi/malawi-steeper-ccocs.json'
portfolioname = '/u/cliffk/unsw/optima/server/src/sim/tests/malawi-gpa-done.npz'
gisfile = '/u/cliffk/unsw/countries/malawi/gis/MWI_adm1'
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
## Plot a map
##################################################################


def plotmap(data, names, gisfile, titles=[''], figsize=(8,8)):
    from pylab import axis, gca, Polygon, show, figure, hold, colorbar, title, scatter, concatenate, ndim, size
    import shapefile as sh
    
    def plotshape(points, color):
        polygon = Polygon(points, color=color)
        gca().add_patch(polygon)
        axis('scaled')
        show()

    # Read in data and get names
    sf = sh.Reader(gisfile)
    numprojects = sf.numRecords
    gisnames = []
    for i in range(numprojects): gisnames.append(sf.record(i)[4])
    
    # Calculate number of maps
    if ndim(data)==1: nmaps = 1
    else: nmaps = size(data,0)
    
    # Process colors
    if nmaps==1:
        colors = [vectocolor(data)]
    else:
        colors = []
        for m in range(nmaps):
            tmp = vectocolor(concatenate(([0], [data.min()], data[m,:], [data.max()])))
            colors.append(tmp[2:-1])
            
    
    # Create figure
    figure(figsize=figsize)
    
    ax = []
    for m in range(nmaps):
        ax.append(subplot(1,nmaps,m+1))
        ax[-1].get_xaxis().set_visible(False)
        ax[-1].get_yaxis().set_visible(False)
        hold(True)
        
        for i,name in enumerate(names):
            try:
                match = gisnames.index(name)
                plotshape(sf.shape(match).points, colors[m][i])
            except:
                print('Name "%s" not matched to GIS file' % name)
        xlims = ax[-1].get_xlim()
        ylims = ax[-1].get_ylim()
        scatter(zeros(len(data.flatten())+1),zeros(len(data.flatten())+1),c=concatenate(([0],data.flatten())))
        ax[-1].set_xlim(xlims)
        ax[-1].set_ylim(ylims)
        title(titles[m])
    
    colorbar()
    
    
    
    




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
    if dosave: savefig('/u/cliffk/unsw/countries/malawi/results/nationalallocation.png', dpi=200)



##################################################################
## Slide 2 -- map of Malawi colored by PLHIV
##################################################################

ndistricts = len(P.gpalist[0])
year = 2015

plhiv = zeros(ndistricts)
prev = zeros(ndistricts)
distnames = []
for d in range(ndistricts):
    R = P.gpalist[0][d].getproject()
    distnames.append(R.getprojectname())
    yearind = findinds(R.simboxlist[0].simlist[0].plotdata['tvec'], year)
    plhiv[d] = array(R.simboxlist[0].simlist[0].plotdata['plhiv']['tot']['best'])[yearind]
    prev[d] = array(R.simboxlist[0].simlist[0].plotdata['prev']['tot']['best'])[yearind]

if makeslide2:
    plotmap(prev, distnames, gisfile, titles=['HIV prevalence per district (%)'], figsize=(6,8))
    if dosave: savefig('/u/cliffk/unsw/countries/malawi/results/prevalencemap.png', dpi=200)
    plotmap(plhiv, distnames, gisfile, titles=['PLHIV per district'], figsize=(6,8))
    if dosave: savefig('/u/cliffk/unsw/countries/malawi/results/plhivmap.png', dpi=200)




##################################################################
## Slide 3 -- map of Malawi colored by spend
##################################################################

factor = 1e6
allocations = zeros((2,ndistricts))
distnames = []
for d in range(ndistricts):
    R = P.gpalist[0][d].getproject()
    distnames.append(R.getprojectname())
    for i in range(2):
        allocations[i,d] = sum(P.gpalist[0][d].simlist[0+2*i].alloc)
    
if makeslide3:
    plotmap(allocations/1e6, distnames, gisfile, titles=['Current spending ($USm)', 'Optimal spending ($USm)'], figsize=(10,8))
    if dosave: savefig('/u/cliffk/unsw/countries/malawi/results/spendingmap.png', dpi=200)



##################################################################
## Slide 4 -- allocations from two different projects
##################################################################

progdata = [0, 0]
for i in range(len(P.gpalist[0])):
    for dist in range(2):
        if P.gpalist[0][i].getproject().getprojectname()==districtstouse[dist]:
            progdata[dist] = P.gpalist[0][i].simlist[2].alloc
if makeslide4:
    plotallocations(progdata, progs, districtstouse, factor=1e3, compare=False)
    if dosave: savefig('/u/cliffk/unsw/countries/malawi/results/districtallocation.png',dpi=200)


print('Done.')