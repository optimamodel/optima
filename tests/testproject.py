"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015nov23 by cliffk
"""



## Define tests to run here!!!
tests = [
'makeproject',
'parametercheck',
'saveload',
#'loadspreadsheet',
#'loadeconomics',
'runsim'
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


## Project creation test
if 'makeproject' in tests:
    t = tic()
    print('Running make project test...')
    from optima import Project
    P = Project()
    print(P)
    done(t)





if 'parametercheck' in tests:
    from optima import defaults, OptimaException
    
    t = tic()
    print('Running parameters check test...')
    
    P = defaults.defaultproject()

    datakeys = P.data.keys()
    datakeys += P.data['const'].keys()
    
    parkeys = P.parsets[0].pars[0].keys()
    
    dataonly = set([
    'condomcas', 'condomcom', 'condomreg', 
    'const', 'hivprev', 'meta', 'npops', 
    'numactscas', 'numactscom', 'numactsinj', 'numactsreg', 
    'optdeath', 'optnewtreat', 'optnumdiag', 'optnuminfect', 'optnumtest', 'optplhiv', 'optprev', 
    'partcas', 'partcom', 'partinj', 'partreg', 
    'pops', 'pships', 'years'])
    
    parsonly = set([
    'actscas', 'actscom', 'actsinj', 'actsreg', 
    'condcas', 'condcom', 'condreg', 
    'female', 'force', 'inhomo', 'initprev', 
    'injects', 'label', 'male', 'popkeys', 'sexworker'])
    
    dataminuspars = set(datakeys) - set(parkeys)
    parsminusdata = set(parkeys) - set(datakeys)
    
    if dataminuspars != dataonly:
        mismatch1 = list(dataonly -  dataminuspars)
        mismatch2 = list(dataminuspars - dataonly)
        errormsg = 'Unexpected "dataminuspars" parameter in "%s" or "%s"' % (mismatch1, mismatch2)
        raise OptimaException(errormsg)
    
    if parsminusdata != parsonly:
        mismatch1 = list(parsonly -  parsminusdata)
        mismatch2 = list(parsminusdata - parsonly)
        errormsg = 'Unexpected "parsminusdata" parameter in "%s" or "%s"' % (mismatch1, mismatch2)
        raise OptimaException(errormsg)
    
    done(t)



## Project save/load test
if 'saveload' in tests:
    t = tic()
    print('Running save/load test...')
    
    from optima import Project, saveobj, loadobj
    from os import remove
    filename = 'testproject.prj'
    
    print('  Checking saving...')
    P = Project()
    saveobj(filename, P)
    
    print('  Checking loading...')
    Q = loadobj(filename)
    
    print('Cleaning up...')
    remove(filename)
    
    done(t)




## Load spreadsheet test
if 'loadspreadsheet' in tests:
    t = tic()
    print('Running loadspreadsheet test...')
    from optima import Project
    
    print('  Create a project from a spreadsheet')
    P = Project(spreadsheet='simple.xlsx')
    
    print('  Load a project, then load a spreadsheet')
    Q = Project()
    Q.loadspreadsheet('simple.xlsx')
    
    assert Q.data['const']['effcondom'][0]==0.95, 'Condom efficacy not 95% or not being read in properly'
    
    done(t)



## Load economics spreadsheet test
if 'loadeconomcs' in tests:
    t = tic()
    print('Running loadeconomics test...')
    from optima import Project
    
    print('  Create an empty project and add economic data')
    P = Project()
    P.loadeconomics(filename='testeconomics.xlsx')

    print('  Create a project from a spreadsheet and add economic data')
    P = Project(spreadsheet='simple.xlsx')
    P.loadeconomics(filename='testeconomics.xlsx')



## Run simulation test
if 'runsim' in tests:
    t = tic()
    print('Running runsim test...')
    
    from optima import Project
    P = Project()
    P.loadspreadsheet('simple.xlsx',dorun=True)
    
    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)