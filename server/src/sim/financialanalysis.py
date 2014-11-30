"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart
"""
import numpy as np
import math
from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, title

def financialanalysis(D, allocation = D.A[0], currentyear = 2014, yscale = 'abs'):
    '''
    Full description to come
    Arguments: 
        1. D
        2. D.A[a_ind] where a_ind = index no. of allocation a
        3. scale \in ['abs', 'gdp', 'revenue', 'totalhealth', domestichealth', 'govtexpend']
    '''
    
    # Interpolate macroeconomic indicators
    if not yscale == 'abs':
        ydenom = []
        for i in range(len(D.data.macro[yscale][0])-1):
            ydenom.extend(np.linspace(D.data.macro[yscale][0][i],D.data.macro[yscale][0][i+1],10,endpoint = False).tolist())
        ydenom.append(D.data.macro[yscale][0][-1])
        ydenom = [ydenom[j] for j in range(len(ydenom))]

    # Get most recent ART unit costs
    progname = 'ART'
    prognumber = D.data.meta.progs.code.index(progname)
    artunitcost = D.data.costcov.cost[prognumber]
    artunitcost = np.asarray(artunitcost)
    artunitcost = artunitcost[~np.isnan(artunitcost)]
    artunitcost = artunitcost[-1]

    # Initiate data storage
    acute, gt500, gt350, gt200, aids, plhiv = [], [], [], [], [], []
    acutetotalcost, gt500totalcost, gt350totalcost, gt200totalcost, aidstotalcost, plhivtotalcost = [], [], [], [], [], []
    
    # Sort out time indexing
    futureindex = np.where(allocation.R.tvec>=currentyear)
    futureindex = futureindex[0].tolist()
    pastindex = np.where(allocation.R.tvec<=currentyear)
    pastindex = pastindex[0].tolist()
    totalindex = allocation.R.tvec

    # What time index do you want to plot with?
    indextoplot = futureindex

    # Calculate total number at each disease stage
    acute = np.sum(np.sum(allocation.S.people[1:5,:,:], axis = 0), axis = 0)
    gt500 = np.sum(np.sum(allocation.S.people[6:10,:,:], axis = 0), axis = 0)
    gt350 = np.sum(np.sum(allocation.S.people[11:15,:,:], axis = 0), axis = 0)
    gt200 = np.sum(np.sum(allocation.S.people[16:20,:,:], axis = 0), axis = 0)
    aids = np.sum(np.sum(allocation.S.people[21:25,:,:], axis = 0), axis = 0)

    # Calculate annual non-treatment costs for PLHIV
    acutetotalcost = [D.data.cost.social.acute[0]*acute[j] for j in range(len(totalindex))]
    gt500totalcost = [D.data.cost.social.gt500[0]*gt500[j] for j in range(len(totalindex))]
    gt350totalcost = [D.data.cost.social.gt350[0]*gt350[j] for j in range(len(totalindex))]
    gt200totalcost = [D.data.cost.social.gt200[0]*gt200[j] for j in range(len(totalindex))]
    aidstotalcost = [D.data.cost.social.aids[0]*aids[j] for j in range(len(totalindex))]

    # Calculate annual treatment costs for PLHIV
    ### TODO: discounting!! ###
    arttotalcost = [(allocation.R.tx1.tot[0][j] + allocation.R.tx2.tot[0][j])*artunitcost for j in range(len(totalindex))]
    plhivannualcost = [acutetotalcost[j] + gt500totalcost[j] + gt350totalcost[j] + gt200totalcost[j] + aidstotalcost[j] + arttotalcost[j] for j in range(len(totalindex))]

    # Cumulative sum function (b/c can't find an inbuilt one)
    def accumu(lis):
        total = 0
        for x in lis:
            total += x
            yield total

    # Calculate annual total costs for PLHIV
    plhivtotalcost = list(accumu(plhivannualcost))
            
    # Calculate future fiscal liabilities
    plhiv = np.sum(np.sum(allocation.S.people[1:25,:,indextoplot], axis = 0), axis = 0)
    futureinfections = D.A[0].R.inci.tot[0][futureindex]
    infections = D.A[0].R.inci.tot[0]
    
    # Set y axis scale and set y axis to the right time period
    if yscale == 'abs':
        ydata1 = plhivannualcost
        ydata2 = plhivtotalcost
    else:
        ydata1 = [plhivannualcost[j] / ydenom[j] for j in range(len(indextoplot))]
        ydata2 = [plhivtotalcost[j] / ydenom[j] for j in range(len(indextoplot))]
    
    # Get x axis for the right time period
    xdata = allocation.R.tvec[indextoplot]

    # Store results
    plotdata = {}
    plotdata['annualhivcosts'] = {}
    plotdata['annualhivcosts']['xlinedata'] = xdata
    plotdata['annualhivcosts']['ylinedata'] = ydata1
    plotdata['annualhivcosts']['title'] = 'Annual healthcare costs over time'
    plotdata['annualhivcosts']['xlabel'] = 'Year'
    plotdata['annualhivcosts']['ylabel'] = 'USD'
    allocation.R.annualhivcosts = plhivannualcost
    
    plotdata['totalhivcosts'] = {}
    plotdata['totalhivcosts']['xlinedata'] = allocation.R.tvec[indextoplot] 
    plotdata['totalhivcosts']['ylinedata'] = ydata2 
    plotdata['totalhivcosts']['title'] = 'Cumulative healthcare costs over time'
    plotdata['totalhivcosts']['xlabel'] = 'Year'
    plotdata['totalhivcosts']['ylabel'] = 'USD'
    allocation.R.totalhivcosts = plhivtotalcost

    # Get financial commitments
    return allocation, plotdata
    
allocation, plotdata = financialanalysis(D, allocation = D.A[0], yscale = 'domestichealth')