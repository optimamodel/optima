# -*- coding: utf-8 -*-
"""
Created on Sat Aug 22 16:38:48 2015

@author: cliffk
"""

import sys; sys.path.append('/u/cliffk/unsw/optima/server/src/sim')
from utils import printdata as pd

from pylab import *
import shapefile as sh

filename = '/u/cliffk/unsw/countries/malawi/gis/MWI_adm0'

sf = sh.Reader(filename)

testshape = sf.shape(0)

x = []
y = []

for p in xrange(len(testshape.points)):
    x.append(testshape.points[p][0])
    y.append(testshape.points[p][1])

figure()
axes()

def plotshape(points, color):
    polygon = Polygon(points, color=color)
    gca().add_patch(polygon)
    axis('scaled')
    show()


points = [[2, 1], [8, 1], [8, 4]]
plotshape(testshape.points, (1,0,0))

print('Done.')