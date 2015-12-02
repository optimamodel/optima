# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 14:59:41 2015

@author: cliffk
"""

from pylab import *
import pickle

ioff()

def plot_axes(ax, fig=None, geometry=(1,1,1)):
    if fig is None: fig = figure()
    ax.change_geometry(*geometry)
    fig.axes.append(ax)
    return fig



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


realfig = figure()
plot_axes(ax1, fig=realfig, geometry=(2,1,1))
plot_axes(ax2, fig=realfig, geometry=(2,1,2))
ax1.set_figure(realfig)
ax2.set_figure(realfig)


#close(fig)

show()

ion()


#f = figure()
#ax = f.add_subplot(111)
#ax.plot([3,4,7])
#title('test')
#op.save('test.fgg',ax)

#z = op.load('test.fgg')


#ax1 = plt.gca()
#scatter([35,34],[24,15])
#ax2 = plt.gca()
#
#
#fig1 = figure()
#plot_axes(z, fig=fig1, geometry=(2,1,1))
#plot_axes(ax2, fig=fig1, geometry=(2,1,2))
#
#fig2 = figure()
#plot_axes(ax1, fig=fig2, geometry=(1,1,1))
#
#show()


#
#
#import matplotlib.pyplot as plt
#import numpy as np
#
#
#
#
#def main():
#    x = np.linspace(0, 6 * np.pi, 100)
#
#    fig1, (ax1, ax2) = plt.subplots(nrows=2)
#    plot(x, np.sin(x), ax1)
#    plot(x, np.random.random(100), ax2)
#
#    fig2 = plt.figure()
#    plot(x, np.cos(x))
#
#    plt.show()
#
#def plot(x, y, ax=None):
#    if ax is None:
#        ax = plt.gca()
#    line, = ax.plot(x, y, 'go')
#    ax.set_ylabel('Yabba dabba do!')
#    return line
#
#if __name__ == '__main__':
#    main()
