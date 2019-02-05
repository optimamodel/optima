# -*- coding: utf-8 -*-
"""
TESTUTILS

A little script for testing various utilities.

Version: 2016jan05 by cliffk
"""


## Define tests to run here!!!
tests = [
'odict',
'gridcolormap',
]



##############################################################################
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore
from pylab import array

if 'doplot' not in locals(): doplot = True

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
    bar = foo.sorted() # Sort the list
    assert(bar['boo'] == 4) # Show get item by value
    assert(bar[1] == 4) # Show get item by index
    assert(array((bar[0:2]) == [3,4]).all()) # Show get item by slice
    assert(array((bar['cough':'dill']) == [6,8]).all()) # Show alternate slice notation
    assert(array((bar[[2,1]]) == [6,4]).all()) # Show get item by list
    assert(array((bar[:]) == [3,4,6,8]).all()) # Show slice with everything
    assert(array((bar[2:]) == [6,8]).all()) # Show slice without end
    bar[3] = [3,4,5] # Show assignment by item
    bar[0:2] = ['the', 'power'] # Show assignment by slice -- NOTE, inclusive slice!!
    bar[[0,2]] = ['cat', 'trip'] # Show assignment by list
    bar.rename('cough','chill') # Show rename
    print(bar) # Print results
    done(t)



## gridcolormap test
if 'gridcolormap' in tests and doplot:
    from mpl_toolkits.mplot3d import Axes3D # analysis:ignore
    t = tic()
    
    from optima import gridcolors
    from pylab import figure, plot, cumsum, rand, legend, show, title
    
    nlines1 = 5
    nlines2 = 12
    npts = 50
    lw = 3 # Line width
    
    colors1 = gridcolors(ncolors=nlines1)
    colors2 = gridcolors(ncolors=nlines2)
    
    fig = figure(figsize=(12,12))
    
    fig.add_subplot(2,2,1)
    for l in range(nlines1): plot(cumsum((rand(npts)+0.1*l)**2), c=colors1[l], lw=lw)
    legend(['%i' % l for l in range(nlines1)], loc='upper left')
    title('<=9 colors: use Color Brewer defaults')
    
    fig.add_subplot(2,2,2)
    for l in range(nlines2): plot(cumsum((rand(npts)+0.1*l)**2), c=colors2[l], lw=lw)
    legend(['%i' % l for l in range(nlines2)], loc='upper left')
    title('>=10 colors: generate based on color cube')
    
    ax = fig.add_subplot(2,2,3, projection='3d')
    gridcolors(ncolors=nlines1, doplot='existing')
    
    ax = fig.add_subplot(2,2,4, projection='3d')
    gridcolors(ncolors=nlines2, doplot='existing')
    
        
    
    done(t)
    show()
