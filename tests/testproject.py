#!/usr/bin/env python

"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016feb03 by cliffk
"""



## Define tests to run here!!!
tests = [
'makeproject',
'parametercheck',
#'resultsaddition',
#'saveload',
'loadspreadsheet',
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
    from optima import defaultproject, OptimaException
    
    t = tic()
    print('Running parameters check test...')
    
    P = defaultproject()

    datakeys = P.data.keys()
    
    parkeys = P.pars().keys()
    
    dataonly = set([
    'condomcas', 'condomcom', 'condomreg', 
    'hivprev', 'meta', 'npops', 
    'numactscas', 'numactscom', 'numactsinj', 'numactsreg', 
    'optdeath', 'optnewtreat', 'optnumdiag', 'optnuminfect', 'optnumtest', 'optplhiv', 'optprev','optpropdx','optpropcare','optproptx','optpropsupp','optproppmtct',
    'partcas', 'partcom', 'partinj', 'partreg', 
    'pops', 'pships', 'years'])
    
    parsonly = set([
    'actscas', 'actscom', 'actsinj', 'actsreg', 'age', 'transnorm',
    'condcas', 'condcom', 'condreg',
    'female', 'force', 'inhomo', 'initprev','hivdeath', 
    'propdx','propcare','proptx','propsupp','proppmtct',
    'injects', 'male', 'popkeys', 'fromto', 'transmatrix',
    'fixproppmtct', 'fixpropsupp', 'fixpropdx', 'fixpropcare', 'fixproptx'])
    
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







## Adding results
if 'resultsaddition' in tests:
    t = tic()
    print('Running results addition test...')
    
    import optima as op

    P = op.defaultproject()
    Q = op.defaultproject()
    
    R1 = P.results[0]
    R2 = Q.results[0]
    
    R3 = R1+R2
    
    if doplot:
        multires = op.Multiresultset([R1,R3])
        op.pygui(multires, toplot=['prev-tot','numplhiv-tot'])
    
    done(t)









## Project save/load test
if 'saveload' in tests:
    t = tic()
    print('Running save/load test...')
    
    from optima import Project, saveobj, loadproj
    from os import remove
    filename = 'testproject.prj'
    
    print('  Checking saving...')
    P = Project()
    saveobj(filename, P)
    
    print('  Checking loading...')
    Q = loadproj(filename)
    
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
    
    assert Q.data['effcondom'][0]==0.95, 'Condom efficacy not 95% or not being read in properly'
    
    done(t)



## Load economics spreadsheet test
if 'loadeconomics' in tests:
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
