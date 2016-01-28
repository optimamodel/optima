"""
Test script to see if geospatial analysis works.
Note that GUI can be extremely dangerous, as it redirects stdout!
Make sure that GUI is exited normally, otherwise stdout reference will be lost until console reset...

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016jan27
"""



## Define tests to run here!!!
tests = [
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



##############################################################################
## The tests
##############################################################################

T = tic()




## Force refresh test
if 'forcerefresh' in tests:
    t = tic()
    print('Running force refresh test...')
    from os import remove
    
    try:
        print('Deleting project files to be used in this test...')
        remove('test7popsARTandHTC.prj')
        remove('test7popsART.prj')
    except OSError:
        print('No relevant project files can be found...')
    
    done(t)




## Project creation test
if 'makeportfolio' in tests:
    t = tic()
    print('Running make portfolio test...')
    from optima import Portfolio, Project, loadobj, dcp
    from optima.defaults import defaultproject
    
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
    from optima import saveobj, defaultobjectives
    
    objectives = defaultobjectives()
#    objectives['inciweight'] = 5
    F.genBOCs(objectives)#,forceregen = True)#, maxtime = 20)
    F.plotBOCs(objectives)    
    
    print('Saving projects with BOCs...')
    saveobj('test7popsFSWandCon.prj', P1)
    saveobj('test7popsCon.prj', P2)
    
    done(t)




if 'rungui' in tests and doplot:
    t = tic()

    print('Running geo GUI test...')
    from optima import geogui
    geogui()
    
    done(t)



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
    