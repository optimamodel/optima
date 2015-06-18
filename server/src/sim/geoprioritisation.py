# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 21:46:25 2015

@author: David Kedziora
"""

import math
from numpy import arange, linspace

def totalobjectivefunc(x, gpasimboxes):
    """Objective function. A secondary argument of all simboxes under gpa must be passed in during minimisation."""
    
    totalobj = 0
    for i in arange(0,len(x)):
        totalobj += gpasimboxes[i](x[i])
    return totalobj
    
def totalobjectivejac(x, gpasimboxes):
    
    totalobjder = np.zeros([len(x)])
    for i in arange(0,len(x)):
        totalobjder[i] = gpasimboxes[i].derivative()(x[i])
    return totalobjder

totalbudget = 300000
def totalbudgetconstraint(t):
    return sum(t) - totalbudget
    

total1 = 100000
total2 = 200000

factors,objarr = ([0.1, 0.2, 0.5, 1, 2, 5],[7420.5665291930309,6895.5487199112631,3774.2076700271682,3708.4290662398462,3618.188538137224,3503.5918712593821])
totals1 = [total1*x for x in factors]
totals2 = [total2*x for x in factors]

# Piecewise Cubic Hermite Interpolating Polynomial (a.k.a. monotonic splines)
from scipy.interpolate import PchipInterpolator as pchip
from scipy.optimize import minimize
import numpy as np
import matplotlib.pyplot as plt

f1 = pchip(totals1, objarr, extrapolate=True)
f2 = pchip(totals2, objarr, extrapolate=True)

xnew = linspace(max(min(totals1),min(totals2)), min(max(totals1),max(totals2)), 500)
plt.plot(xnew,f1(xnew),'-',xnew,f2(xnew),'--')
plt.legend(['totals1','totals2'], loc='best')
plt.show()

plt.plot(xnew,f1.derivative()(xnew),'-',xnew,f2.derivative()(xnew),'--')
plt.show()

print totalobjectivefunc([125000,175000],[f1,f2])
print totalobjectivejac([125000,175000],[f1,f2])

cons = ({'type': 'eq',
         'fun' : totalbudgetconstraint})
         
res = minimize(totalobjectivefunc, [100000,200000], args=([f1,f2]), jac=totalobjectivejac,               
               constraints=cons, tol=1e-15, options={'disp': True})