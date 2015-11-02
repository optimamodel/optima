"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

Version: 2015nov01 by cliffk
"""



## Define tests to run here!!!
tests = [
'makespreadsheet',
'makeproject',
'saveload',
'loadspreadsheet',
'runsim',
]

numericalassertions = True # Whether or not to actually run things and test their values
doplot = True # Whether or not to show diagnostic plots



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
if 'makespreadsheet' in tests:
    t = tic()
    print('Running make spreadsheet test...')
    from makespreadsheet import makespreadsheet
    makespreadsheet()
    done(t)



## Project creation test
if 'makeproject' in tests:
    t = tic()
    print('Running make project test...')
    from project import Project
    P = Project()
    print(P)
    done(t)




## Project save/load test
if 'saveload' in tests:
    t = tic()
    print('Running save/load test...')
    
    from project import Project, load
    filename = 'testproject.prj'
    
    print('  Checking saving...')
    P = Project()
    P.save(filename)
    
    print('  Checking loading...')
    Q = load(filename)
    Q.save()
    Q.loadfromfile()
    
    print('  Checking defaults...')
    Z = Project()
    Z.save()
    
    done(t)




## Load spreadsheet test
if 'loadspreadsheet' in tests:
    t = tic()
    print('Running loadspreadsheet test...')
    from project import Project
    
    print('  Create a project from a spreadsheet')
    P = Project(spreadsheet='test.xlsx')
    
    print('  Load a project, then load a spreadsheet')
    Q = Project()
    Q.loadspreadsheet('test.xlsx')
    
    if numericalassertions:
        assert Q.data['const']['effcondom'][0]==0.05, 'Condom efficacy not 95% or not being read in properly'
    
    done(t)




## Run simulation test
if 'runsim' in tests:
    t = tic()
    print('Running runsim test...')
    
    from pylab import plot, xlabel, ylabel, show
    from project import Project
    P = Project(spreadsheet='test.xlsx')
    S = P.runsim('default')
    if doplot:
        plot(S['tvec'], S['people'][0,0,:])
        xlabel('Year')
        ylabel('Number of susceptibles')
        show()
    
    done(t)







print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)