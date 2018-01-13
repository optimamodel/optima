"""
Test script to see if geospatial analysis works.
Note that GUI can be extremely dangerous, as it redirects stdout!
Make sure that GUI is exited normally, otherwise stdout reference will be lost until console reset...

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2017mar19
"""



## Define tests to run here!!!
tests = [
'makespreadsheet',
'runGA',
#'geogui',
]

dosave = False # Whether or not to keep generated spreadsheets

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



## Make spreadsheet test
if 'makespreadsheet' in tests:
    t = tic()
    print('Running makeprojects...')
    from optima import makegeospreadsheet, defaultproject
    from os import remove
    spreadsheetpath = 'simple-ga-division-template.xlsx'
    P = defaultproject('simple')
    makegeospreadsheet(project=P, filename=spreadsheetpath, copies=2, refyear=2015)
    if not dosave: remove(spreadsheetpath)
    done(t)
   


## Make projects test
if 'runGA' in tests:
    t = tic()
    print('Running GA...')
    from optima import makegeoprojects, defaultproject, defaultobjectives, Portfolio
    from os import remove
    
    # Definitions
    spreadsheetpath = 'subdivision.xlsx'
    outputpath = 'simple-ga-results.xlsx'
    
    # Make projects
    P = defaultproject('simple')
    projlist = makegeoprojects(project=P, spreadsheetpath=spreadsheetpath, dosave=False)
    
    # Make portfolio and run
    F = Portfolio(projects=projlist, objectives=defaultobjectives())
    F.objectives['end'] = 2020 # This speeds it up by only simulating 3 years
    F.genBOCs(maxtime=1, mc=0, budgetratios=[1.0, 0.5, 2.0]) # Generate BOCs
    F.runGA(maxtime=1, mc=0) # Run GA
    F.export(filename=outputpath) # Export
    
    # Tidy
    if not dosave: remove(outputpath)
    if doplot: F.plotBOCs()
    done(t)





if 'geogui' in tests and doplot:
    t = tic()

    print('Running geo GUI test...')
    from optima import geogui
    
    instructions = '''
    Instructions for testing the geogui:
    
    1. Create a simple project (P = defaultproject('simple'); P.save())
    2. Click "Make geospatial spreadsheet from project" and save it somewhere
    3. Click "Auto-generate projects from spreadsheet", select the simple
       project, and select tests/subdivision.xlsx, and save the projects somewhere
    4. Click "Create portfolio from projects", and select the two you just created
    5. Click "Run geospatial analysis". It should take about 2 minutes.
    6. Click "Export results'
    '''
    print(instructions)
    geogui()
    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
    