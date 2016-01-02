# -*- coding: utf-8 -*-
"""
TESTUTILS

A little script for testing various utilities.

Version: 2015nov21 by cliffk
"""


## Define tests to run here!!!
tests = [
'odict',
'gridcolormap',
]



##############################################################################
## Initialization
##############################################################################

from utils import tic, toc, blank, pd # analysis:ignore

def done(t=0):
    print('Done.')
    toc(t)
    blank()
    





blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()




##############################################################################
## The tests
##############################################################################

T = tic()



## Spreadsheet creation test
if 'odict' in tests:
    t = tic()
    print('Running odict tests...')
    from optima import odict
    foo = odict({'ah':3,'boo':4, 'cough':6, 'dill': 8})
    bar = foo.sort() # Sort the list
    assert(bar['boo'] == 4) # Show get item by value
    assert(bar[1] == 4) # Show get item by index
    assert((bar[0:2] == [3,4]).all()) # Show get item by slice
    assert((bar['cough':'dill'] == [6,8]).all()) # Show alternate slice notation
    assert(bar[[2,1]] == [6,4]) # Show get item by list
    bar[3] = [3,4,5] # Show assignment by item
    bar[0:1] = ['the', 'power'] # Show assignment by slice -- NOTE, inclusive slice!!
    bar.rename('cough','chill') # Show rename
    print(bar) # Print results
    done(t)



## gridcolormap test
if 'gridcolormap' in tests:
    from mpl_toolkits.mplot3d import Axes3D
    t = tic()
    
    from optima import gridcolormap
    from pylab import figure, plot, cumsum, rand, legend
    
    nlines1 = 5
    nlines2 = 12
    npts = 50
    lw = 3 # Line width
    
    colors1 = gridcolormap(ncolors=nlines1)
    colors2 = gridcolormap(ncolors=nlines2)
    
    fig = figure(figsize=(12,12))
    
    fig.add_subplot(2,2,1)
    for l in range(nlines1): plot(cumsum((rand(npts)+0.1*l)**2), c=colors1[l], lw=lw)
    legend(['%i' % l for l in range(nlines1)], loc='upper left')
    
    fig.add_subplot(2,2,2)
    for l in range(nlines2): plot(cumsum((rand(npts)+0.1*l)**2), c=colors2[l], lw=lw)
    legend(['%i' % l for l in range(nlines2)], loc='upper left')
    
    fig.add_subplot(2,2,3, projection='3d')
    gridcolormap(ncolors=nlines1, doplot=True, newwindow=False)
    fig.add_subplot(2,2,4, projection='3d')
    gridcolormap(ncolors=nlines2, doplot=True, newwindow=False)
        
    
    done(t)
