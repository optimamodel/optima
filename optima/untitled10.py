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
        
        exponents = [1e9, 1e6, 1e3]
        labels = ['b', 'm', 'k']
        
        for i,exponent in enumerate(exponents):
            if x>=exponent: 
#                x = round(x/exponent) if x>=exponent*10 else round(10*x/exponent)/10
                x /= exponent
                suffix = labels[i]

        origlocs = dcp(self.locs)
        self.locs = [loc/exponent for loc in self.locs]
        orig = ScalarFormatter.__call__(self, x, pos)
#        self.locs = origlocs
        print('hi')
        print x
        print orig
        print pos
#        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
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
