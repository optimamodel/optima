# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 21:46:25 2015

@author: David Kedziora
"""

from numpy import arange, linspace
#from scipy.optimize import minimize

# The object returned by getBOCspline() is a pchip. See SimBoxOpt.
#from scipy.interpolate import PchipInterpolator as pchip

#def totalobjectivefunc(xin, (gpasimboxes, grandtotal)):
#    """Objective function. A secondary argument of all simboxes under gpa must be passed in during minimisation."""
#
#    x = [xin[i]*scalingfactors[i] for i in arange(0,len(xin))]    
#    
#    l = x[-1]    # Lagrangian multiplier
#    
#    totalobj = 0
#    for i in arange(0,len(x)-1):
#        totalobj += (gpasimboxes[i].getBOCspline().derivative()(x[i]) + l)**2
#    totalobj += (sum(x[:-1])-grandtotal)**2
#    print totalobj
#    return totalobj
    
def testobjectivefunc(xin, (gpapchips, grandtotal)):
    """Objective function. A secondary argument of all pchips under gpa must be passed in during minimisation."""
    x = [xi*grandtotal/sum(xin) for xi in xin]
    
    totalobj = 0
    for i in arange(0,len(x)):
        totalobj += gpapchips[i](x[i])
    print totalobj
    return totalobj
    
#def totalobjectivefunc(x, gpasimboxes):
#    """Objective function. A secondary argument of all simboxes under gpa must be passed in during minimisation."""
#    
#    totalobj = 0
#    for i in arange(0,len(x)):
#        totalobj += gpasimboxes[i].getBOCspline()(x[i])
#    return totalobj
    
#def totalobjectivejac(x, gpasimboxes):
#    
#    totalobjder = zeros([len(x)])
#    for i in arange(0,len(x)):
#        totalobjder[i] = gpasimboxes[i].getBOCspline().derivative()(x[i])
#    return totalobjder

#totalbudget = 300000
#def totalbudgetconstraint(t):
#    return sum(t) - totalbudget
#    
#
#total1 = 100000
#total2 = 200000
#
#factors,objarr = ([0.1, 0.2, 0.5, 1, 2, 5],[7420.5665291930309,6895.5487199112631,3774.2076700271682,3708.4290662398462,3618.188538137224,3503.5918712593821])
#totals1 = [total1*x for x in factors]
#totals2 = [total2*x for x in factors]
#
## Piecewise Cubic Hermite Interpolating Polynomial (a.k.a. monotonic splines)
#from scipy.interpolate import PchipInterpolator as pchip
#from scipy.optimize import minimize
#import numpy as np
#import matplotlib.pyplot as plt
#
#f1 = pchip(totals1, objarr, extrapolate=True)
#f2 = pchip(totals2, objarr, extrapolate=True)
#
#xnew = linspace(max(min(totals1),min(totals2)), min(max(totals1),max(totals2)), 500)
#plt.plot(xnew,f1(xnew),'-',xnew,f2(xnew),'--')
#plt.legend(['totals1','totals2'], loc='best')
#plt.show()
#
#plt.plot(xnew,f1.derivative()(xnew),'-',xnew,f2.derivative()(xnew),'--')
#plt.show()
#
#print totalobjectivefunc([125000,175000],[f1,f2])
#print totalobjectivejac([125000,175000],[f1,f2])
#
#cons = ({'type': 'eq',
#         'fun' : totalbudgetconstraint})
#         
#res = minimize(totalobjectivefunc, [100000,200000], args=([f1,f2]), jac=totalobjectivejac,               
#               constraints=cons, tol=1e-15, options={'disp': True})

GIB = 14746612.0
HIB = 220650283.0
GBOCx = [1474661.2, 2949322.4, 7373305.999999999, 14746611.999999998, 29493223.999999996, 73733059.99999999]
GBOCy = [7420.566529193031, 6895.548719803941, 3774.207669823583, 3708.429066239846, 3618.188538137224, 3503.591871259382]
HBOCx = [22065028.3, 44130056.6, 110325141.5, 220650283.0, 441300566.0, 1103251415.0]
HBOCy = [25005.62384682375, 23444.48190211528, 18266.5441001453, 17310.937016319283, 17312.31503529964, 17312.550566584538]

from scipy.interpolate import PchipInterpolator as pchip

GS = pchip(GBOCx, GBOCy, extrapolate=True)
HS = pchip(HBOCx, HBOCy, extrapolate=True)

import matplotlib.pyplot as plt

#xnew = linspace(max(min(GBOCx),min(HBOCx)), min(max(GBOCx),max(HBOCx)), 500)
xnew = linspace(0, min(max(GBOCx),max(HBOCx)), 500)
plt.plot(xnew,GS(xnew),'-',xnew,HS(xnew),'--')
plt.legend(['Georgia','Haiti'], loc='best')
plt.show()

plt.plot(xnew,GS.derivative()(xnew),'-',xnew,HS.derivative()(xnew),'--')
plt.legend(['Georgia','Haiti'], loc='best')
plt.show()

from ballsd import ballsd

grandtotal = GIB + HIB
XOUT, FVAL, EXITFLAG, OUTPUT = ballsd(testobjectivefunc, [GIB, HIB], options=([GS,HS], grandtotal), xmin = [0,0], xmax = [grandtotal, grandtotal])
X = [xi*grandtotal/sum(XOUT) for xi in XOUT]


def gpaoptimisefixedtotal(simboxref):
#    budgettotals = zeros([len(simboxref)+1])
    budgettotals = []
    minbound = []
    for i in arange(0,len(simboxref)):
        print simboxref[i].getlatestalloc()
        budgettotals.append(sum(simboxref[i].getlatestalloc()))
        minbound.append(0)
    grandtotal = sum(budgettotals)
    print budgettotals
    
#    # The constraint is that all region budgets must add up to the same amount.
#    def totalbudgetconstraint(t):
#        return sum(t) - grandtotal
#        
#    def totalbudgetconstraintjac(t):
#        return ones([len(t)])
#    
#    cons = ({'type': 'eq',
#         'fun' : totalbudgetconstraint})#,
##         'jac' : totalbudgetconstraintjac})
#
#    print 'Yo'
#    print totalobjectivefunc(budgettotals,(simboxref,grandtotal))
##    print totalobjectivejac(budgettotals,simboxref)
#    print 'No'
         
#    res = minimize(totalobjectivefunc, budgettotals, args=(simboxref), jac=totalobjectivejac,               
#               bounds=[(0,None) for x in simboxref], constraints=cons, options={'disp': True})
               
    from ballsd import ballsd
    
    budgettotals.append(0)    # Lagrange multiplier initial guess.
    minbound.append(None)     # Lagrange multiplier minimum.
    X, FVAL, EXITFLAG, OUTPUT = ballsd(totalobjectivefunc, budgettotals, options=(simboxref, grandtotal), xmin = minbound)
               
    print X
    print FVAL
    print EXITFLAG
    print OUTPUT