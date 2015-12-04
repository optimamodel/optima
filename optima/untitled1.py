# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 14:59:41 2015

@author: cliffk
"""

from pylab import *
import pickle

ion()

fig1 = figure()
ax1 = subplot(111)
x1 = linspace(0, 10)
y1 = exp(x1)
title('plot1')
plt.plot(x1, y1)
pickle.dump(fig1, file('plot1.fgg', 'w'))
close(fig1)

fig2 = figure()
ax2 = subplot(111)
x2 = linspace(0, 10)
y2 = x2**2
title('plot2')
plt.plot(x2, y2)
pickle.dump(fig2, file('plot2.fgg', 'w'))
close(fig2)

fld1 = pickle.load(file('plot1.fgg'))
fld2 = pickle.load(file('plot2.fgg'))
close(fld1)
close(fld2)

ld1 = fld1.axes[0]
ld2 = fld2.axes[0]


realfig, (ax3, ax4) = subplots(1, 2)
realfig._axstack.remove(ax3)
realfig._axstack.remove(ax4)

#ld1.set_figure(realfig)
#ld2.set_figure(realfig)

#ld1.set_position(ax3.get_position())
#ld2.set_position(ax4.get_position())

realfig._axstack.add(realfig._make_key(ld1), ld1)
realfig._axstack.add(realfig._make_key(ld2), ld2)



#ax.get_position()

ld1.change_geometry(2,1,1)
ld2.change_geometry(2,1,2)
