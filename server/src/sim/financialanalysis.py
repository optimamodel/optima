"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart
"""
import numpy as np
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title

def financialanalysis(D, sim = D, yscale = 'abs', makeplot = True):
    '''
    Full description to come
    Arguments: 
        1. D
        2. simulation to plot results of. For example, could be D, D.A[0], etc
        3. yscale chosen from ['abs', 'gdp', 'revenue', 'totalhealth', domestichealth', 'govtexpend']
    '''
    
    # Interpolate macroeconomic indicators 
    if not yscale == 'abs':
        ydenom = []
        for i in range(len(D.data.macro[yscale][0])-1):
            ydenom.extend(np.linspace(D.data.macro[yscale][0][i],D.data.macro[yscale][0][i+1],10,endpoint = False).tolist())
        ydenom.append(D.data.macro[yscale][0][-1])
        ydenom = [ydenom[j] for j in range(len(ydenom))]

    # Interpolate time
    xdata1 = np.arange(D.data.econyears[0], D.data.econyears[-1]+D.opt.dt, D.opt.dt)
    xdata2 = np.arange(D.data.econyears[1], D.data.econyears[-1]+D.opt.dt, D.opt.dt)
    npts1, npts2 = len(xdata1), len(xdata2)

    # Get most recent ART unit costs
    progname = 'ART'
    prognumber = D.data.meta.progs.short.index(progname)
    artunitcost = D.data.costcov.cost[prognumber]
    artunitcost = np.asarray(artunitcost)
    artunitcost = artunitcost[~np.isnan(artunitcost)]
    artunitcost = artunitcost[-1]

    # Calculate total number in each disease stage
    acute = np.sum(np.sum(sim.S.people[1:5,:,:], axis = 0), axis = 0)
    gt500 = np.sum(np.sum(sim.S.people[6:10,:,:], axis = 0), axis = 0)
    gt350 = np.sum(np.sum(sim.S.people[11:15,:,:], axis = 0), axis = 0)
    gt200 = np.sum(np.sum(sim.S.people[16:20,:,:], axis = 0), axis = 0)
    aids = np.sum(np.sum(sim.S.people[21:25,:,:], axis = 0), axis = 0)

    # Calculate number of new infections... 
    inf = np.sum(sim.S.people[1,:,:], axis = 0)

    # Calculate number added at each time period to each disease stage
    newacute = [j-i for i, j in zip(acute[:-1], acute[1:])]
    newgt500 = [j-i for i, j in zip(gt500[:-1], gt500[1:])]
    newgt350 = [j-i for i, j in zip(gt350[:-1], gt350[1:])]
    newgt200 = [j-i for i, j in zip(gt200[:-1], gt200[1:])]
    newaids = [j-i for i, j in zip(aids[:-1], aids[1:])]

    # Calculate annual non-treatment costs for all PLHIV
    acutetotalcost = [D.data.cost.social.acute[0]*acute[j] for j in range(npts1)]
    gt500totalcost = [D.data.cost.social.gt500[0]*gt500[j] for j in range(npts1)]
    gt350totalcost = [D.data.cost.social.gt350[0]*gt350[j] for j in range(npts1)]
    gt200totalcost = [D.data.cost.social.gt200[0]*gt200[j] for j in range(npts1)]
    aidstotalcost = [D.data.cost.social.aids[0]*aids[j] for j in range(npts1)]

    # Calculate annual non-treatment costs for all PLHIV
    acutenewcost = [D.data.cost.social.acute[0]*newacute[j] for j in range(npts2)]
    gt500newcost = [D.data.cost.social.gt500[0]*newgt500[j] for j in range(npts2)]
    gt350newcost = [D.data.cost.social.gt350[0]*newgt350[j] for j in range(npts2)]
    gt200newcost = [D.data.cost.social.gt200[0]*newgt200[j] for j in range(npts2)]
    aidsnewcost = [D.data.cost.social.aids[0]*newaids[j] for j in range(npts2)]

    # Calculate annual treatment costs for PLHIV
    ### TODO: discounting!! ###
    onart = [sim.R.tx1.tot[0][j] + sim.R.tx2.tot[0][j] for j in range(npts1)]
    arttotalcost = [onart[j]*artunitcost for j in range(npts1)]
    
    # Calculate annual treatment costs for new PLHIV
    newpeopleonart = [j-i for i,j in zip(onart[:-1],onart[1:])]
    artnewcost = [newpeopleonart[j]*artunitcost for j in range(npts2)]

    # Calculate annual total costs for all and new PLHIV
    annualhivcosts = [acutetotalcost[j] + gt500totalcost[j] + gt350totalcost[j] + gt200totalcost[j] + aidstotalcost[j] + arttotalcost[j] for j in range(npts1)]
    annualhivcostsfuture = [acutenewcost[j] + gt500newcost[j] + gt350newcost[j] + gt200newcost[j] + aidsnewcost[j] + artnewcost[j] for j in range(npts2)]

    # Cumulative sum function (b/c can't find an inbuilt one)
    def accumu(lis):
        total = 0
        for x in lis:
            total += x
            yield total

    # Calculate cumulative total costs for PLHIV
    cumulhivcosts = list(accumu(annualhivcosts))
    cumulhivcostsfuture = list(accumu(annualhivcostsfuture))
            
    # Set y axis scale and set y axis to the right time period
    if yscale == 'abs':
        ydata1 = annualhivcosts
        ydata2 = cumulhivcosts
        ydata3 = annualhivcostsfuture
        ydata4 = cumulhivcostsfuture
    else:
        ydata1 = [annualhivcosts[j] / ydenom[j] for j in range(npts1)]
        ydata2 = [cumulhivcosts[j] / ydenom[j] for j in range(npts1)]
        ydata3 = [annualhivcostsfuture[j] / ydenom[j] for j in range(npts2)]
        ydata4 = [cumulhivcostsfuture[j] / ydenom[j] for j in range(npts2)]

    # Store results
    plotdata = {}
    plotdata['annualhivcosts'] = {}
    plotdata['annualhivcosts']['xlinedata'] = xdata1
    plotdata['annualhivcosts']['ylinedata'] = ydata1
    plotdata['annualhivcosts']['title'] = 'Annual healthcare costs over time'
    plotdata['annualhivcosts']['xlabel'] = 'Year'
    plotdata['annualhivcosts']['ylabel'] = 'USD'
    sim.R.annualhivcosts = annualhivcosts
    
    plotdata['cumulhivcosts'] = {}
    plotdata['cumulhivcosts']['xlinedata'] = xdata1
    plotdata['cumulhivcosts']['ylinedata'] = ydata2 
    plotdata['cumulhivcosts']['title'] = 'Cumulative healthcare costs over time'
    plotdata['cumulhivcosts']['xlabel'] = 'Year'
    plotdata['cumulhivcosts']['ylabel'] = 'USD'
    sim.R.cumulhivcosts = cumulhivcosts

    plotdata['annualhivcostsfuture'] = {}
    plotdata['annualhivcostsfuture']['xlinedata'] = xdata2
    plotdata['annualhivcostsfuture']['ylinedata'] = ydata3
    plotdata['annualhivcostsfuture']['title'] = 'Annual healthcare costs for post-2015 infections'
    plotdata['annualhivcostsfuture']['xlabel'] = 'Year'
    plotdata['annualhivcostsfuture']['ylabel'] = 'USD'

    plotdata['cumulhivcostsfuture'] = {}
    plotdata['cumulhivcostsfuture']['xlinedata'] = xdata2
    plotdata['cumulhivcostsfuture']['ylinedata'] = ydata4
    plotdata['cumulhivcostsfuture']['title'] = 'Cumulative healthcare costs for post-2015 infections'
    plotdata['cumulhivcostsfuture']['xlabel'] = 'Year'
    plotdata['cumulhivcostsfuture']['ylabel'] = 'USD'

    if makeplot:
        figure()
        hold(True)
        plot(plotdata['cumulhivcosts']['xlinedata'], plotdata['cumulhivcosts']['ylinedata'], lw = 2)
        title(plotdata['cumulhivcosts']['title'])
        xlabel('Year')
        ylabel('USD')

    # Get financial commitments
    return sim, plotdata
    
#example
#sim, plotdata = financialanalysis(D, sim = D, yscale = 'abs')
