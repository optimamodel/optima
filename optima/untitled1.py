# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 14:59:41 2015

@author: cliffk
"""

from pylab import *
import pickle

ioff()

tmpfig = figure()
ax1 = subplot(111)
x1 = linspace(0, 10)
y1 = exp(x1)
title('plot1')
plt.plot(x1, y1)
pickle.dump(ax1, file('plot1.fgg', 'w'))
close(tmpfig)

tmpfig = figure()
ax2 = subplot(111)
x2 = linspace(0, 10)
y2 = x2**2
title('plot2')
plt.plot(x2, y2)
pickle.dump(ax2, file('plot2.fgg', 'w'))
close(tmpfig)

ld1 = pickle.load(file('plot1.fgg'))
ld2 = pickle.load(file('plot2.fgg'))
close(ld1.get_figure())
close(ld2.get_figure())



realfig, (ax3, ax4) = subplots(1, 2, figsize=(10,5))

ld1.set_subplotspec(ax3.get_subplotspec())
ld2.set_subplotspec(ax4.get_subplotspec())

realfig._axstack.remove(ax3)
realfig._axstack.remove(ax4)
realfig._axstack.add(realfig._make_key(ld1), ld1)
realfig._axstack.add(realfig._make_key(ld2), ld2)

ld1.change_geometry(2,1,1)
ld2.change_geometry(2,1,2)

show()
