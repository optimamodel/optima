"""
Test script to see if geospatial analysis works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016jan31
"""



## Define tests to run here!!!
tests = [
'makeprojects',
#'forcerefresh',
#'makeportfolio',
#'generateBOCs',
'rungui',
]

##############################################################################
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore

if 'doplot' not in locals(): doplot = True

def done(t=0):
    print('Done.')
    toc(t)
    blank()

blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()

filename1 = 'test1.prj'
filename2 = 'test2.prj'


##############################################################################
## The tests
##############################################################################

T = tic()



## Make projects test
if 'makeprojects' in tests:
    t = tic()
    print('Running makeprojects...')
    from optima import saveobj, defaults
    
    P = defaults.defaultproject('generalized', name='District 1')
    Q = defaults.defaultproject('concentrated', name='District 2')
    O = defaults.defaultproject('concentrated', name='District 3')
    saveobj('geotestproj1.prj', P)
    saveobj('geotestproj2.prj', Q)
    saveobj('geotestproj3.prj', O)
    
    done(t)



## Force refresh test
if 'forcerefresh' in tests:
    t = tic()
    print('Running force refresh test...')
    from os import remove
    
    try:
        print('Deleting project files to be used in this test...')
        remove(filename1)
        remove(filename2)
    except OSError:
        print('No relevant project files can be found...')
    
    done(t)




## Project creation test
if 'makeportfolio' in tests:
    t = tic()
    print('Running make portfolio test...')
    from optima import Portfolio, loadobj
    from optima.defaults import defaultproject
    
    try:
        P1 = loadobj(filename1)
        P2 = loadobj(filename2)
    except:
        P1 = defaultproject('concentrated')
        P2 = defaultproject('concentrated')
    
        P1.progsets[0].rmprogram('OST')
        P2.progsets[0].rmprogram('OST')
        P2.progsets[0].rmprogram('HTC')

    F = Portfolio(projects=[P1,P2])

    done(t)




## BOC generation test
if 'generateBOCs' in tests:
    t = tic()

    print('Running BOC generation test...')
    from optima import saveobj
    
    F.genBOCs(progsetnames=['default','default'], parsetnames=['default','default'], maxtime=3)#,forceregen = True)#, maxtime = 20)
    F.plotBOCs()
    
    print('Saving projects with BOCs...')
    saveobj(filename1, P1)
    saveobj(filename2, P2)
    
    done(t)




if 'rungui' in tests and doplot:
    t = tic()

    print('Running geo GUI test...')
    from optima import geogui
    geogui()
    
    done(t)



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
    