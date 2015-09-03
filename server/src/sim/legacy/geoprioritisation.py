# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 21:46:25 2015

@author: David Kedziora
"""

from numpy import arange
from ballsd import ballsd

# Simple scaling of budget totals to adhere to fixed grand total constraint.
# Must also adhere to minimum bound constraints.
def constrainbudgetinputs(x, grandtotal, minbound):
    
    # First make sure all values are not below the respective minimum bounds.
    for i in xrange(len(x)):
        if x[i] < minbound[i]:
            x[i] = minbound[i]
    
    # Then scale all excesses over the minimum bounds so that the new sum is grandtotal.
    constrainedx = []
    for i in xrange(len(x)):
        xi = (x[i] - minbound[i])*(grandtotal - sum(minbound))/(sum(x) - sum(minbound)) + minbound[i]
        constrainedx.append(xi)
    
    return constrainedx

# Total objective function to minimise is just the sum of BOC values for a set of projectal budget totals.
def totalobjectivefunc(x, (projectlist, grandtotal, minbound)):
    """Objective function. A secondary argument of all simboxes under gpa must be passed in during minimisation."""
    x = constrainbudgetinputs(x, grandtotal, minbound)
    
    totalobj = 0
    for i in arange(0,len(x)):
        totalobj += projectlist[i].getBOCspline()(x[i])
    print totalobj
    return totalobj

def gpaoptimisefixedtotal(projectlist):
    
    # Start by working out initial (projectal budget total) inputs to perturb from, including their sum.
    budgettotals = []
    for i in arange(0,len(projectlist)):
        print('Original allocation for project %s:' % projectlist[i].getprojectname())
        projectlist[i].printprograms()
        print(projectlist[i].getorigalloc())
        budgettotals.append(sum(projectlist[i].getorigalloc()))
    grandtotal = sum(budgettotals)
    minbound = [r.returnfixedcostsum() for r in projectlist]
    maxbound = [grandtotal]*len(projectlist)
    # print budgettotals
    
               
    X, FVAL, EXITFLAG, OUTPUT = ballsd(totalobjectivefunc, budgettotals, options=(projectlist, grandtotal, minbound), xmin = minbound, xmax = maxbound)
    X = constrainbudgetinputs(X, grandtotal, minbound)
    
    # Display GPA results for debugging purposes.
    totinobj = 0
    totoptobj = 0
    for i in arange(0,len(projectlist)):
        projectname = projectlist[i].getprojectname()
        inobj = projectlist[i].getBOCspline()(budgettotals[i])
        optobj = projectlist[i].getBOCspline()(X[i])
        totinobj += inobj
        totoptobj += optobj
        print('Project %s...' % projectname)
        print('Initial Budget Total: $%.2f' % budgettotals[i])
        print('Optimised Budget Total: $%.2f' % X[i])
        print('Initial Objective: %f' % inobj)
        print('Optimised Objective: %f' % optobj)
        try:
            print('Initial BOC Derivative: %.3e' % projectlist[i].getBOCspline().derivative()(budgettotals[i]))
            print('Optimised BOC Derivative: %.3e\n' % projectlist[i].getBOCspline().derivative()(X[i]))
        except:
            print('BOC derivatives not available')
    print('GPA Portfolio Results...')
    print('Initial Budget Grand Total: $%.2f' % sum(budgettotals))
    print('Optimised Budget Grand Total: $%.2f' % sum(X))
    print('Initial Objective Total: %f' % totinobj)
    print('Optimised Objective Total: %f\n' % totoptobj)
    
    return X

## Hard coded test of BALLSD-based GPA.
#def testobjectivefunc(xin, (gpapchips, grandtotal)):
#    """Objective function. A secondary argument of all pchips under gpa must be passed in during minimisation."""
#    x = [xi*grandtotal/sum(xin) for xi in xin]
#    
#    totalobj = 0
#    for i in arange(0,len(x)):
#        totalobj += gpapchips[i](x[i])
#    print totalobj
#    return totalobj
#
#GIB = 14746612.0
#HIB = 220650283.0
#GBOCx = [1474661.2, 2949322.4, 7373305.999999999, 14746611.999999998, 29493223.999999996, 73733059.99999999]
#GBOCy = [7420.566529193031, 6895.548719803941, 3774.207669823583, 3708.429066239846, 3618.188538137224, 3503.591871259382]
#HBOCx = [22065028.3, 44130056.6, 110325141.5, 220650283.0, 441300566.0, 1103251415.0]
#HBOCy = [25005.62384682375, 23444.48190211528, 18266.5441001453, 17310.937016319283, 17312.31503529964, 17312.550566584538]
#
#from scipy.interpolate import PchipInterpolator as pchip
#
#GS = pchip(GBOCx, GBOCy, extrapolate=True)
#HS = pchip(HBOCx, HBOCy, extrapolate=True)
#
#import matplotlib.pyplot as plt
#from numpy import linspace
#
##xnew = linspace(max(min(GBOCx),min(HBOCx)), min(max(GBOCx),max(HBOCx)), 500)
#xnew = linspace(0, min(max(GBOCx),max(HBOCx)), 500)
#plt.plot(xnew,GS(xnew),'-',xnew,HS(xnew),'--')
#plt.legend(['Georgia','Haiti'], loc='best')
#plt.show()
#
#plt.plot(xnew,GS.derivative()(xnew),'-',xnew,HS.derivative()(xnew),'--')
#plt.legend(['Georgia','Haiti'], loc='best')
#plt.show()
#
#grandtotal = GIB + HIB
#XOUT, FVAL, EXITFLAG, OUTPUT = ballsd(testobjectivefunc, [GIB, HIB], options=([GS,HS], grandtotal), xmin = [0,0], xmax = [grandtotal, grandtotal])
#X = [xi*grandtotal/sum(XOUT) for xi in XOUT]