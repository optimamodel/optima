# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths # analysis:ignore
from portfolio import Portfolio
from region import Region
import os
from copy import deepcopy

from numpy import array, sort
from timevarying import timevarying

# Create a Portfolio to hold all of Malawi's districts (i.e. Regions).
p1 = Portfolio('Malawi Project')

#nationcheck = Region.load('./regions/Malawi 150820.json')

# List all the json files in the regions sub-directory.
templist = sort([x for x in os.listdir('./regions/') if x.endswith('.json')])

r1 = Region.load('./regions/' + templist[0])

p1.appendregion(r1)
sb1 = r1.createsimbox('sb-test-sim', isopt = True, createdefault = False)

# From [i['short_name'] for i in r1.metadata['inputprograms']]
#             0       1                2                 3        4     5          6         7            8      9      10        11    12         13     14                15
programs = [u'VMMC', u'FSW programs', u'MSM programs', u'HTC', u'ART', u'PMTCT', u'OVC', u'Other care', u'MGMT', u'HR', u'ENV', u'SP', u'M&E', u'Other', u'Condoms & SBCC', u'CT']


somealloc1 = array([  69.,   11.,    1.,  231.,  # 0-3
                     9905.,  314.,  117.,  224.,  # 4-7
                     758.,   97.,   78.,   70.,  # 8-11
                     180.,  202.,  181.,   28.   # 12-15
                     ])*1e6


somealloc2 = deepcopy(somealloc1)/1e9
somealloc2[4] = somealloc1[4] # ART

somebudget1 = timevarying(somealloc1, ntimepm = 1, nprogs = len(somealloc1), tvec = r1.options['partvec'])
somebudget2 = timevarying(somealloc2, ntimepm = 1, nprogs = len(somealloc2), tvec = r1.options['partvec'])

s1 = sb1.createsim('test1', budget = somebudget1, forcecreate = True)
s1.plotresults()
s2 = sb1.createsim('test2', budget = somebudget2, forcecreate = True)
s2.plotresults()
sb1.viewmultiresults()

#reglimit = 40    # How many districts do you want to load?
#
#calc = 0
#regcount = 0
#for x in templist:
#    # Make sure you only select files with the right format (i.e. Regex 4 Dummies).
#    if x[:-5].replace(" ", "").isalpha():
#        regcount += 1
#        print x
#        newregion = Region.load('./regions/' + x)           # Load up a Region from the json file.
#        p1.appendregion(newregion)                          # Put that Region into a Portfolio.
#        print('Region alloc total: %f' % sum(newregion.data['origalloc']))       
#        calc += sum(newregion.data['origalloc'])
#        
#        # A way to load only the first few files you want.        
#        if regcount == reglimit:
#            break
#print('Region alloc total sum: %f' % calc)
#print('Nation alloc total: %f' % sum(nationcheck.data['origalloc']))
#
## Ignore this. It helps you run a simulation and an optimisation for a region of your choice.
#def testsimopt(r1):
#
#    r1.createsimbox('sb-test-sim', isopt = False, createdefault = True)
#    r1.simboxlist[-1].runallsims()
#    
#    r1.createsimbox('sb-test-opt', isopt = True, createdefault = True)
#    r1.simboxlist[-1].runallsims()
#    
#    r1.simboxlist[0].viewmultiresults()
#    r1.simboxlist[-1].viewmultiresults()
#    
#    print
#    print('%30s%15s' % ('Unoptimised...', 'Optimised...'))
#    for x in xrange(len(r1.metadata['inputprograms'])):
#        print('%-15s%15.2f%15.2f' % (r1.metadata['inputprograms'][x]['short_name']+':',
#                                     r1.simboxlist[-1].simlist[0].alloc[x],
#                                     r1.simboxlist[-1].simlist[-1].alloc[x]))
#                                     
## Use this if you want to check GPA results for any region, numbered from 1 to 32.
## Only run this if you have run geoprioanalysis.
#def check(x):
#    sb = p1.gpalist[-1][x-1]    
#    
#    print(sb.getregion().getregionname())
#
#    sb.getregion().plotsimbox(sb, multiplot = True)
#    
#    r = sb.getregion()
#    regionname = r.getregionname()
#
#    print('Region %s...' % regionname)
#    sumin = sum(sb.simlist[0].alloc)
#    sumopt = sum(sb.simlist[1].alloc)
#    sumgpaopt = sum(sb.simlist[2].alloc)
#    estsuminobj = r.getBOCspline()([sumin])
#    estsumoptobj = r.getBOCspline()([sumopt])
#    estsumgpaoptobj = r.getBOCspline()([sumgpaopt])
#    realsuminobj = sb.simlist[0].calculateobjectivevalue()
#    realsumoptobj = sb.simlist[1].calculateobjectivevalue(normaliser = sb.simlist[0])
#    realsumgpaoptobj = sb.simlist[2].calculateobjectivevalue(normaliser = sb.simlist[0])
#    
#    import matplotlib.pyplot as plt
#    ax = r.plotBOCspline(returnplot = True)
#    ms = 10
#    mw = 2
#    ax.plot(sumopt, estsumoptobj, 'x', markersize = ms, markeredgewidth = mw, label = 'Init. Opt. Est.')
#    ax.plot(sumopt, realsumoptobj, '+', markersize = ms, markeredgewidth = mw, label = 'Init. Opt. Real')
#    ax.plot(sumgpaopt, estsumgpaoptobj, 'x', markersize = ms, markeredgewidth = mw, label = 'GPA Opt. Est.')
#    ax.plot(sumgpaopt, realsumgpaoptobj, '+', markersize = ms, markeredgewidth = mw, label = 'GPA Opt. Real')
#    ax.legend(loc='best')
#    plt.show()
#    
#    if sumin == sumopt:
#        print('Initial Unoptimised/Optimised Budget Total: $%.2f' % sumin)
#    else:
#        print('Initial Unoptimised Budget Total: $%.2f' % sumin)
#        print('Initial Optimised Budget Total: $%.2f' % sumopt)
#    print('GPA Optimised Budget Total: $%.2f' % sumgpaopt)
#    print
#    if not sumin == sumopt: print('Initial Unoptimised Objective Estimate (BOC): %f' % estsuminobj)
#    print('Initial Optimised Objective Estimate (BOC): %f' % estsumoptobj)
#    print('GPA Optimised Objective Estimate (BOC): %f' % estsumgpaoptobj)
#    print
#    if not sumin == sumopt: print('Initial Unoptimised BOC Derivative: %.3e' % r.getBOCspline().derivative()(sumin))
#    print('Initial Optimised BOC Derivative: %.3e' % r.getBOCspline().derivative()(sumopt))
#    print('GPA Optimised BOC Derivative: %.3e' % r.getBOCspline().derivative()(sumgpaopt))
#    print
#    print('Initial Unoptimised Real Objective: %f' % realsuminobj)
#    print('Initial Optimised Real Objective: %f' % realsumoptobj)
#    print('GPA Optimised Real Objective: %f' % realsumgpaoptobj)
#    print('BOC Estimate was off for %s objective by: %f (%f%%)' % (regionname, estsumgpaoptobj-realsumgpaoptobj, 100*abs(estsumgpaoptobj-realsumgpaoptobj)/realsumgpaoptobj))
#    print('\n')
#    
#    
#    print('%40s%20s%20s' % ('Unoptimised...', 'Optimised...', 'GPA Optimised...'))
#    for x in xrange(len(r.metadata['inputprograms'])):
#        print('%-20s%20.2f%20.2f%20.2f' % (r.metadata['inputprograms'][x]['short_name']+':',r.simboxlist[-1].simlist[0].alloc[x],r.simboxlist[-1].simlist[1].alloc[x],r.simboxlist[-1].simlist[2].alloc[x]))
#    print('\n')
#    
## Recalculate BOC for region numbered between 1 and 32.
#def refine(x):
#    p1.refineregionBOC(p1.regionlist[x-1])
#    
#def refineall():
#    for x in xrange(len(p1.regionlist)):
#        refine(x+1)
#    
#    p1.quicksaveregions()
#
##testsimopt(newregion)
#
#p1.geoprioanalysis()                # Run the GPA algorithm.
#
##p1.geoprioreview(p1.gpalist[0])     # Did those results go by too quickly? Review the plots and a results summary.
