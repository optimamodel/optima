# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 21:46:25 2015

@author: David Kedziora
"""

from numpy import arange, zeros, ones
from scipy.optimize import minimize

# The object returned by getBOCspline() is a pchip. See SimBoxOpt.
#from scipy.interpolate import PchipInterpolator as pchip

def totalobjectivefunc(x, (gpasimboxes, grandtotal)):
    """Objective function. A secondary argument of all simboxes under gpa must be passed in during minimisation."""
    """Input x contains len(x)-1 budget totals, while x[len(x)] is a lagrangian multiplier."""
    
    l = x[-1]    # Lagrangian multiplier
    
    totalobj = 0
    for i in arange(0,len(x)-1):
        totalobj += (gpasimboxes[i].getBOCspline().derivative()(x[i]) + l)**2
    totalobj += (sum(x[:-1])-grandtotal)**2
    print totalobj
    return totalobj
    
#def totalobjectivefunc(x, gpasimboxes):
#    """Objective function. A secondary argument of all simboxes under gpa must be passed in during minimisation."""
#    
#    totalobj = 0
#    for i in arange(0,len(x)):
#        totalobj += gpasimboxes[i].getBOCspline()(x[i])
#    return totalobj
    
def totalobjectivejac(x, gpasimboxes):
    
    totalobjder = zeros([len(x)])
    for i in arange(0,len(x)):
        totalobjder[i] = gpasimboxes[i].getBOCspline().derivative()(x[i])
    return totalobjder

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
    
    # The constraint is that all region budgets must add up to the same amount.
    def totalbudgetconstraint(t):
        return sum(t) - grandtotal
        
    def totalbudgetconstraintjac(t):
        return ones([len(t)])
    
    cons = ({'type': 'eq',
         'fun' : totalbudgetconstraint})#,
#         'jac' : totalbudgetconstraintjac})

    print 'Yo'
    print totalobjectivefunc(budgettotals,(simboxref,grandtotal))
#    print totalobjectivejac(budgettotals,simboxref)
    print 'No'
         
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