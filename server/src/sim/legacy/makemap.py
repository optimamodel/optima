"""
Created on Sat Aug 22 16:38:48 2015

@author: cliffk
"""

import sys; sys.path.append('/u/cliffk/unsw/optima/server/src/sim')
from utils import printdata as pd # analysis:ignore
from pylab import axis, gca, Polygon, show, figure, axes, hold
import shapefile as sh

filename = '/u/cliffk/unsw/countries/malawi/gis/MWI_adm1'


def plotshape(points, color):
    polygon = Polygon(points, color=color)
    gca().add_patch(polygon)
    axis('scaled')
    show()


sf = sh.Reader(filename)

numprojects = sf.numRecords

figure()
ax = axes(frameon=False)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
hold(True)

from gridcolormap import gridcolormap
colors = gridcolormap(numprojects)

for r in xrange(numprojects):
    plotshape(sf.shape(r).points, colors[r])


names = []
for i in range(numprojects): names.append(sf.record(i)[4])

print('Done.')