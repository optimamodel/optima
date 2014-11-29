"""
Created on Sat Nov 29 17:40:34 2014

@author: robynstuart
"""
import numpy as np

def financialanalysis(D, allocation = D.A[0], yscale = 'abs'):
    '''
    Full description to come
    Arguments: 
        1. D
        2. D.A[a_ind] where a_ind = index no. of allocation a
        3. scale \in ['abs', 'gdp', 'revenue', 'totalhealth', domestichealth', 'govtexpend']
    '''
    
    # Expand macroeconomic indicators if necessary
    if not yscale == 'abs':
        ydenom = []
        for i in range(len(D.data.macro[yscale][0])-1):
            ydenom.extend(np.linspace(D.data.macro[yscale][0][i],D.data.macro[yscale][0][i+1],10,endpoint = False).tolist())
        ydenom.extend(D.data.macro[yscale][0][-1])

    
    # Get last year's unit costs of ART
    progname = 'ART'
    prognumber = D.data.meta.progs.code.index(progname)
    artunitcost = D.data.costcov.cost[prognumber]
    artunitcost = asarray(artunitcost)
    artunitcost = artunitcost[~isnan(artunitcost)]
    artunitcost = artunitcost[-1]

    # Initiate data storage
    acute, gt500, gt350, gt200, aids, plhiv, = [], [], [], [], [], []
    acutetotalcost, gt500totalcost, gt350totalcost, gt200totalcost, aidstotalcost, plhivtotalcost = [], [], [], [], [], []

    # Calculate total number at each disease stage. Includes people not on treatment... 
    acute = np.sum(np.sum(allocation.S.people[2:5][:][:], axis = 0),axis=0)
    gt500 = np.sum(np.sum(allocation.S.people[7:10][:][:], axis = 0),axis=0)
    gt350 = np.sum(np.sum(allocation.S.people[12:15][:][:], axis = 0),axis=0)
    gt200 = np.sum(np.sum(allocation.S.people[17:20][:][:], axis = 0),axis=0)
    aids = np.sum(np.sum(allocation.S.people[22:25][:][:], axis = 0),axis=0)
    plhiv = np.sum(np.sum(allocation.S.people[1:25][:][:], axis = 0),axis=0)
#        infections = np.sum(allocation.S.inci, axis = 0)
    
    # Calculate annual total costs associated with PLHIV, including non-treatment costs
    acutetotalcost = [(D.data.cost.social.acute[0] + artunitcost)*acute[j] for j in range(len(acute))]
    gt500totalcost = [(D.data.cost.social.gt500[0] + artunitcost)*gt500[j] for j in range(len(gt500))]
    gt350totalcost = [(D.data.cost.social.gt350[0] + artunitcost)*gt350[j] for j in range(len(gt350))]
    gt200totalcost = [(D.data.cost.social.gt200[0] + artunitcost)*gt200[j] for j in range(len(gt200))]
    aidstotalcost = [(D.data.cost.social.aids[0] + artunitcost)*aids[j] for j in range(len(aids))]
    plhivtotalcost = [acutetotalcost[j] + gt500totalcost[j] + gt350totalcost[j] + gt200totalcost[j] + aidstotalcost[j] for j in range(len(acute))]
        
    ### TODO: discounting!! ###
        
    # Set y axis scale
    if yscale == 'abs':
        ydata = plhivtotalcost
    else:
        ydata = [plhivtotalcost[j] / ydenom[j] for j in range(len(allocation.R.tvec))]

    # Store results
    plotdata = {}
    plotdata['xlinedata'] = allocation.R.tvec # X data for all line plots
    plotdata['ylinedata'] = ydata # ALL Y data (for three lines)
    plotdata['title'] = 'Annual healthcare costs over time'
    plotdata['xlabel'] = 'Year'
    plotdata['ylabel'] = 'USD'
    allocation.R.hivcosts = plhivtotalcost

    return allocation, plotdata
    
