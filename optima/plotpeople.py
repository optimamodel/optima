# -*- coding: utf-8 -*-
"""
Simple little code to visualize the people in the people array.

@author: cliffk
"""

import matplotlib as mpl
from pylab import hold, shape, subplot, figure, title, ylabel, plot

def plotpeople(resultslist):
    if type(resultslist) is not list: resultslist = [resultslist]
    ppl = resultslist[0].people
    statelabels = []
    statelabels.append('sus1')
    statelabels.append('sus2')
    cd4s = ['a', '500', '350', '200', '50', '0']
    types = ['ud', 'dx', 'tx']
    for t in types:
        for cd4 in cd4s:
            statelabels.append(t+cd4)
    nstates = len(statelabels) # 
    if nstates != shape(ppl)[0]:
        raise Exception("Number of states don't match")
    npops = shape(ppl)[1]
    count = 0
    figh = figure(figsize=(24,16), facecolor='w')
    figh.subplots_adjust(left=0.02, right=0.99, top=0.97, bottom=0.01, wspace=0.00, hspace=0.00) # Less space
    
    mpl.rcParams.update({'font.size': 8})
    eps = 1e-9
    for s in range(nstates):
        for p in range(npops):
            count += 1
            h = subplot(nstates, npops, count)
            hold(True)
            for z in range(len(resultslist)):
                ppl = resultslist[z].people
                plot(resultslist[z].tvec, ppl[s,p,:]/(ppl[s,p,:].max()+eps)) # Plot values normalized across everything
            h.set_xticks([])
            h.set_yticks([])
            h.set_ylim((0, 1.1))
            if s==0: title('Population %i' % p)
            if p==0: ylabel('%s' % statelabels[s])