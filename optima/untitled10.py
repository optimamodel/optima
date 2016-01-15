# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 16:22:42 2016

@author: cliffk
"""

from matplotlib.ticker import ScalarFormatter

from pylab import *
from copy import deepcopy as dcp

class SIsuffix(ScalarFormatter):
    ''' Format axis tick values like 23k, 1.4m, etc. '''
    def __call__(self, x, pos=None):
        suffix = ''
        
        exponents = [9, 6, 3]
        labels = ['b', 'm', 'k']
        thisexponent = None
        
        # Get the original formatting
        orig = ScalarFormatter.__call__(self, x, pos)
        
        for i,exponent in enumerate(exponents):
            if x>=10**exponent: 
                if suffix=='': 
                    thisexponent = exponent
                    suffix = labels[i]
#        killzeros = thisexponent
#        while killzeros>0:
#            if orig.find('.')==-1 and 
#
#        
#        orig
        return orig+suffix
        


def setSIticks(axis=None, x=False, y=True):
    theseaxes = []
    if x: theseaxes.append(axis.get_xaxis())
    if y: theseaxes.append(axis.get_yaxis())
    for thisaxis in theseaxes:
        thisaxis.set_major_formatter(SIsuffix())
        thisaxis.get_major_formatter().set_scientific(False)
        thisaxis.get_major_formatter().set_useOffset(False)
    return None
        

fig = figure()
plot([23343293,23522301])
axis = gca()
setSIticks(axis)

#axis.get_yaxis().set_major_formatter(SIsuffix())
#axis.get_yaxis().get_major_formatter().set_scientific(False)
