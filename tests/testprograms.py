"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016feb06
"""



## Define tests to run here!!!
tests = [
#'loadprogramspreadsheet', # TEMPORARILY NON-FUNCTIONAL
'demonstrateprogrammethods',
'addpopfactor',
#'plotprogram',
'compareoutcomes',
#'reconcilepars',
]


##############################################################################
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore
from numpy.testing import assert_allclose

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

# Set tolerance levels
eps = 1e-2
atol = 1e-2
rtol = 1e-2

##############################################################################
## The tests
##############################################################################






if 'loadprogramspreadsheet' in tests:
    t = tic()
    
    print('Loading programs spreadsheet ...')
    from optima import defaultproject

    P = defaultproject('best',addprogset=True,addcostcovdata=False,addcostcovpars=False,addcovoutpars=True)
    R = P.progsets[0]
    filename = 'testprogramdata.xlsx'
    R.loadspreadsheet(filename)    
    done()



## Demonstrate and test programs methods
if 'demonstrateprogrammethods' in tests:
    t = tic()

    print('Demonstrating typical programs methods...')
    from optima import defaultproject
    P = defaultproject('best',addprogset=True,addcostcovdata=True,addcostcovpars=True)
    R = P.progsets[0]
    progs = P.programs()
    HTS = progs['HTS']

    # 1. Get parameters for defining cost-coverage function for any given year (even if not explicitly entered).
    HTS.costcovfn.getccopar(2014)

    # 2. Get target population size
    HTS.gettargetpopsize(t=[2013,2015],parset=P.parsets['default'])

    # 3. Evaluate cost-coverage function to get coverage for a given year, spending amount and population size
    from numpy import linspace, array
    HTS.getcoverage(x=linspace(0,1e6,3),t=[2013,2015,2017],parset=P.parsets['default'],total=False)
    HTS.targetcomposition = {'Clients': array([ 0.01]),
                       'F 15+': array([ 0.3]),
                       'FSW': array([ 0.12]),
                       'PWID': array([ 0.12]),
                       'M 15+': array([ 0.3]),
                       'MSM': [ 0.15]}
    
    # Make sure that getcoverage and getbudget are the reciprocal of each other.
    a = HTS.getcoverage(x=1e6,t=2016,parset=P.parsets['default'])
    b = HTS.getbudget(x=a,t=2016,parset=P.parsets['default'])
    assert_allclose(1e6,b,rtol=rtol)
    # NB, if you want to evaluate it for a particular population size, can also do...
    HTS.costcovfn.evaluate(x=[1e6],popsize=[1e5],t=[2015],toplot=False)

    # 3. Get default budget and coverage
    defaultbudget = R.getdefaultbudget()
    defaultcoverage = R.getdefaultcoverage(t=2016, parset=P.parsets['default'])

    R.getprogcoverage(budget=defaultbudget,
                      t=2016,
                      parset=P.parsets['default'])
                        
    R.getprogbudget(coverage=defaultcoverage,
                      t=2016,
                      parset=P.parsets['default'])
                        
    R.getpopcoverage(budget=defaultbudget,
                      t=2016,
                     parset=P.parsets['default'])

    # 4. Get a dictionary of only the program-affected parameters corresponding to a dictionary of program allocations or coverage levels
    outcomes = R.getoutcomes(coverage=defaultcoverage,
                      t=2016,
                                parset=P.parsets['default'])
    
    R.getoutcomes(defaultcoverage, t=2016, parset=P.parsets['default'])
    R.getoutcomes(t=2016, parset=P.parsets['default'])
            

    # 5. Get an odict of the ALL parameter values corresponding to a vector of program allocations
    P.addprogset(name='default', progset=R)
    P.runbudget(budget=defaultbudget, budgetyears=2016, progsetname='default', parsetname='default')
    
    done(t)



## Add population adjustment factors
if 'addpopfactor' in tests:

    P = defaultproject('best',dorun=False)
    
    cov1 = P.progsets[-1].getprogcoverage(budget=P.progsets[-1].getdefaultbudget(),
                      t=2016,
                      parset=P.parsets['default'])
    
    P.progsets[-1].programs[0].costcovfn.ccopars['popfactor'] = .2

    cov2 = P.progsets[-1].getprogcoverage(budget=P.progsets[-1].getdefaultbudget(),
                      t=2016,
                      parset=P.parsets['default'])
    
    print(cov1)
    print(cov2)
    


## Try program plotting
if 'plotprogram' in tests:
    P = defaultproject('best',addprogset=True,addcostcovdata=True,addcostcovpars=True)
    R = P.progsets[0]
    progs = P.programs()
    HTS = progs['HTS']
    caption = 'Spending data includes all HTS spending. Global Fund spending on HTS in 2012 was $40,245. '\
                  'In the reporting period, a total of 676 MARPs received HTS services, which makes a cumulative '\
                  'total of 1,102 MARPs that received HTS including provision of results. Due to changes in '\
                  'the definition and focus of the indicator, PWID that received HTS in DST Centers and prisoners '\
                  'are included, both of them previously omitted in the reports.'
    plotoptions = {}
    plotoptions['caption'] = caption
    plotoptions['xupperlim'] = 2e9
    plotoptions['perperson'] = False

    if doplot:
        HTS.plotcoverage(t=[2014,2015],parset=P.parsets['default'],plotoptions=plotoptions,doplot=doplot)




## Project creation test
if 'compareoutcomes' in tests:
    P = defaultproject('best',addprogset=True,addcostcovdata=True,addcostcovpars=True)
    comparison = P.progsets[0].compareoutcomes(parset=P.parsets[0], year=2016, doprint=True)
    done(t)



# Reconciliation test
if 'reconcilepars' in tests:
    import optima as op
    P = op.defaultproject('best')
    ps = P.parsets[0]

    before = op.dcp(P.progsets[0])
    P.progsets[0].reconcile(parset=ps, year=2016, maxtime=3, uselimits=True)
    after = P.progsets[0]
    print('\n\nBEFORE:')
    before.compareoutcomes(parset=ps, year=2016, doprint=True)
    print('\n\nAFTER:')
    after.compareoutcomes(parset=ps, year=2016, doprint=True)
    



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)