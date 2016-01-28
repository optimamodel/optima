"""
Test script to see if geospatial analysis works.
Note that GUI can be extremely dangerous, as it redirects stdout!
Make sure that GUI is exited normally, otherwise stdout reference will be lost until console reset...

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016jan20 by davidkedz
"""



## Define tests to run here!!!
tests = [
#'forcerefresh',
'makeportfolio',
'generateBOCs',
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
    F = Portfolio()
    
    P1 = defaultproject('concentrated')
    P2 = defaultproject('concentrated')

    P1.progsets[0].rmprogram('OST')
    P2.progsets[0].rmprogram('OST')
    P2.progsets[0].rmprogram('HTC')

    F.addproject(P1)
    F.addproject(P2)
    print(F)
    done(t)




## BOC generation test
if 'generateBOCs' in tests:
    t = tic()

    print('Running BOC generation test...')
    from optima import Project, saveobj
    from optima import defaultobjectives
    
    objectives = defaultobjectives()
    F.genBOCs(objectives)
    F.plotBOCs(objectives)    
    
    print('Saving projects with BOCs...')
    saveobj('test7popsARTandHTC.prj', P1)
    saveobj('test7popsART.prj', P2)
    
    done(t)




if 'rungui' in tests and doplot:
    from optima import Project, Portfolio, geogui, saveobj
    
    P = Project(spreadsheet='simple.xlsx')
    Q = Project(spreadsheet='simple.xlsx')
    F = Portfolio()
    for proj in [P, Q]: F.addproject(proj)
    saveobj('test2.prj', P)
    saveobj('test7.prj', Q)
    saveobj('test.prt', F)
    print('Opening geospatial GUI. It will run after tests are completed.')



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)

# The actual GUI is delayed until after the rest of test output, otherwise that too will be displayed in the widget.
if 'rungui' in tests and doplot:
    geogui()