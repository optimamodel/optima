# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 18:31:43 2015

@author: cliffk
"""

from pylab import *
import mpld3

ioff()

fig1 = figure()
ax1 = fig1.add_subplot(111)
pl1 = plot([3,4,7])

fig2 = figure()
ax2 = fig2.add_subplot(211)
plot([3,4,23])
ax2 = fig2.add_subplot(212)
plot([23,25])


mpld3.show()