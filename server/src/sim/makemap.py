# -*- coding: utf-8 -*-
"""
Created on Sat Aug 22 16:38:48 2015

@author: cliffk
"""

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

scatter(x,y)

print('Done.')