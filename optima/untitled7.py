# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 01:05:32 2015

@author: cliffk
"""

from pylab import *
start = 2000
t = array([2000, 2005, 2008, 2050])
y = array([14, 17, 18, 50])
p = polyfit(t-start, log(y), 1)
p = [exp(p[1]), p[0]]
figure()
plot(t,log(y))

figure()
scatter(t,y)
hold(True)
T = linspace(t[0],t[-1])
Y = p[0]*exp((T-start)*p[1])
plot(T,Y)
