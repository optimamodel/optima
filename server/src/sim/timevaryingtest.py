"""
Simple test for time-varying optimisation:
    
    2 parameter works fine -- OK to use 
    3 and 4 are playing up -- something to do with element-wise powers

Written by Roo
"""

from timevarying import timevarying
from matplotlib.pylab import figure, plot, hold, ylim, show
from numpy import linspace

nprogs = 3

allocpm = [500, 150, 250, -5, 10, 2]

startyr = 2010
endyr   = 2030
timestp = 0.2

t = linspace(startyr, endyr, (endyr - startyr) / timestp + 1)

totalspend = sum(allocpm[:nprogs])

alloc = timevarying(allocpm, ntimepm=2, nprogs=nprogs, t=t, totalspend=totalspend)

figure(1)

for prog in range(nprogs):
    plot(t, alloc[prog, :])
    hold(True)
    
plot(t, alloc.sum(axis=0), color='k', linewidth=3)

ylim(ymin=0, ymax=totalspend+100)

show()

