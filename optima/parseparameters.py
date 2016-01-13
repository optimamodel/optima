# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 17:47:36 2016

@author: cliffk
"""

from optima import *
from pylab import *

filename = 'tmpparameters.csv'

P = Project(spreadsheet='test.xlsx')

pars = P.parsets[0].pars[0]
allattributes = []
allpars = []
for item in pars.values()+pars['const'].values():
    if isinstance(item, Par):
        allpars.append(item)
        allattributes += item.__dict__.keys()

allattributes = set(allattributes)
print(allattributes)


attrs = ['name', 'short', 'fittable', 'auto', 'limits', 'by', 'type']
allparprops = []
for par in allpars:
    thisparprops = {}
    for attr in attrs:
        try: thisparprops[attr] = getattr(par, attr)
        except: pass
        thisparprops['type'] = type(par).__name__
    allparprops.append(thisparprops)

fmt = '%25s,'
out = ''
for at in attrs:
    out += fmt % at
out += '\n'
for pardict in allparprops:
    for at in attrs:
        out += fmt % str(pardict[at])
    out += '\n'


with open(filename, 'w') as f: f.write(out)
print('Done.')