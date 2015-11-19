"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015nov01 by cliffk
"""



## Define tests to run here!!!
tests = [
'makespreadsheet',
'makeproject',
'saveload',
'loadspreadsheet',
'runsim',
'gui'
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
    
    from utils import save, load
    from project import Project
    filename = 'testproject.prj'
    
    print('  Checking saving...')
    P = Project()
    save(P, filename)
    
    print('  Checking loading...')
    Q = load(filename)
    
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
if 'runsim' or 'gui' in tests:
    t = tic()
    print('Running runsim test...')
    
    from project import Project
    P = Project(spreadsheet='test.xlsx')
    results = P.runsim('default')
    
    done(t)





## Run the GUI
if 'gui' in tests:
    t = tic()
    print('Running GUI test...')
    
    try:
        from gui import gui
        gui(results)
    except:
        print('Backend GUI failed to load -- not critical')
    
    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)