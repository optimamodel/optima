"""
Tests to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Unlike the other test files, these tests are designed to be run sequentially, 
and are not intended to be comprehensive, but rather show the key workflow.

Version: 2016jan29
"""



## Define tests to run here!!!
tests = [
#'minimal'
#'makeproject',
#'makeprograms',
#'autofit',
'manualfit',
#'plotresults',
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

T = tic()


##############################################################################
## The tests
##############################################################################

if 'minimal' in tests:
    t = tic()
    print('Running minimal test...')
    
    from optima import Project
    P = Project(spreadsheet='simple.xlsx')
    
    done(t)




#####################################################################################################
if 'makeproject' in tests:
    t = tic()
    print('Running makeproject/runsim test...')
    
    from optima import Project
    P = Project(spreadsheet='generalized.xlsx')
    P.loadeconomics(filename='testeconomics.xlsx')
    results = P.runsim('default')
    
    done(t)





#####################################################################################################
if 'makeprograms' in tests:
    t = tic()

    print('Making a default programset...')
    from optima.defaults import defaultprogset
    R = defaultprogset(P, addpars=True, addcostcov=True, filterprograms=['Condoms', 'FSW programs', 'MSM programs', 'HTC', 'ART', 'PMTCT', 'MGMT', 'HR', 'Other']) #TODO Add ART, PMTCT, VMMC
    
    # Modify target pars and pops
    R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'M 0-14'})
    R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'F 0-14'})
    R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('M 0-14'))
    R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('F 0-14'))
    R.updateprogset()

    # Add program effects
    R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
    R.covout['condcas'][('FSW', 'Clients')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
    R.covout['condcas'][('Clients', 'F 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 15-49','Clients')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65), 'MSM_programs':(0.75,0.85)})
    R.covout['condcas'][('M 15-49', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
    R.covout['condcas'][('FSW', 'M 15-49')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
    R.covout['condcas'][('M 15-49', 'F 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 15-49', 'M 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 50+', 'M 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('M 50+', 'F 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 50+', 'Clients')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('Clients', 'F 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('M 50+', 'FSW')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('FSW', 'M 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('M 15-49', 'F 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 50+', 'M 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 15-49', 'M 50+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('M 50+', 'F 15-49')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})

    R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW_programs':(0.9,0.95)})
    R.covout['condcom'][('FSW', 'Clients')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW_programs':(0.9,0.95)})

    R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99), 'FSW_programs':(0.95,0.99)})
    R.covout['hivtest']['MSM'].addccopar({'intercept': (0.05,0.1), 't': 2016.0, 'HTC': (0.95,0.99), 'MSM_programs':(0.95,0.99)})
    R.covout['hivtest']['Clients'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['M 15-49'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['F 15-49'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['M 50+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['F 50+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})

    R.covout['numtx']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
    R.covout['numpmtct']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})

    budget = R.getdefaultbudget()
    coverage = R.getprogcoverage(budget=budget, t=2016, parset=P.parsets['default'])
    outcomes = R.getoutcomes(coverage=coverage, t=2016, parset=P.parsets['default'])
    
    done(t)













#####################################################################################################
if 'autofit' in tests:
    t = tic()

    print('Running autofit test...')
    P.autofit(name='autofit', orig='default', what=['force', 'init'], maxtime=None, maxiters=50, inds=None) # Run automatic fitting
    P.loadeconomics(filename='testeconomics.xlsx')
    results = P.runsim('autofit', end=2015)
    
    done(t)






#####################################################################################################
## Manual calibration test
#####################################################################################################
if 'manualfit' in tests and doplot:
    t = tic()

    print('Running manual calibration test...')
    if 'P' not in locals():
        import optima
        P = optima.defaults.defaultproject()
    P.manualfit(orig=-1, name='manual') # Demonstrating that you can retrieve things by index as well
    
    done(t)





#####################################################################################################
## Plot results test
#####################################################################################################
if 'plotresults' in tests and doplot:
    t = tic()

    print('Running results plotting test...')
    from optima import plotresults
    plotresults(P.results[-1], toplot=['prev-tot', 'numinci-sta'], figsize=(16,10)) # Showing kwargs passed to plot
    
    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)