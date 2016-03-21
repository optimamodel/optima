# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 12:35:57 2016

@author: David Kedziora
"""

from optima import *
from numpy import arange

cid = 0

p = loadobj('malawi.prt')
g = p.gaoptims[0]
rp = g.resultpairs[cid]

tvector = rp['init'].tvec
initial = findinds(tvector, g.objectives['start'])
final = findinds(tvector, g.objectives['end'])
indices = arange(initial, final)

outdeath = rp['init'].main['numdeath'].tot[0][indices].sum()
outinci = rp['init'].main['numinci'].tot[0][indices].sum()
improv = rp['init'].improvement[-1][0]

print(outdeath)
print(outinci)
print(outdeath*5 + outinci)
print(improv)

outdeath = rp['opt'].main['numdeath'].tot[-1][indices].sum()
outinci = rp['opt'].main['numinci'].tot[-1][indices].sum()
improv = rp['opt'].improvement[-1][-1]

print(outdeath)
print(outinci)
print(outdeath*5 + outinci)
print(improv)