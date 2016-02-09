"""
Load Zambia and create outcome functions
"""

## Define tests to run here!!!
tests = [
'loadzambia',
'addeffects',
'compareepi'
'compareoutcomes',
'savezambia',
]

##############################################################################
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore

if 'doplot' not in locals(): doplot = True
showstats = True

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


## Load Zambia project
if 'loadzambia' in tests:
    t = tic()


    from optima import loadobj
    filename = 'exercise_complete-1.prj'
    
    P = loadobj(filename)

    P.runsim()

    done(t)

## Add program effects
if 'addeffects' in tests:
    
    R = P.progsets[0]
    
    # Circumcision
    R.covout['numcirc']['Clients'].addccopar({'intercept': (0,0), 't': 2016.0})
    R.covout['numcirc']['MSM'].addccopar({'intercept': (0,0), 't': 2016.0})
    R.covout['numcirc']['Males 0-14'].addccopar({'intercept': (0,0), 't': 2016.0})
    R.covout['numcirc']['Males 15-24'].addccopar({'intercept': (0,0), 't': 2016.0})
    R.covout['numcirc']['Males 25-49'].addccopar({'intercept': (0,0), 't': 2016.0})
    R.covout['numcirc']['Males 50+'].addccopar({'intercept': (0,0), 't': 2016.0})
    
    # Commercial condom use
    R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.5,0.6), 't': 2016.0, 'FSW programs':(0.9,0.95)})

    # Treatment
    R.programs['PMTCT'].rmtargetpar({'param': u'numtx', 'pop': u'tot'})
    R.updateprogset()
    R.covout['numtx']['tot'].addccopar({'intercept': (0.,0.), 't': 2016.0})
    
    # PMTCT
    R.covout['numpmtct']['tot'].addccopar({'intercept': (0.,0.), 't': 2016.0})
    
    # Casual condom use
    R.covout['condcas'][('Females 50+', 'Males 50+')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Males 15-24', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Females 25-49', 'Clients')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Males 25-49', 'Females 15-24')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'MSM programs':(0.45,0.55)})
    R.covout['condcas'][('Females 25-49', 'Males 15-24')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Females 50+', 'Males 25-49')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Females 15-24', 'Clients')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Males 25-49', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Males 50+', 'Females 25-49')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Females 15-24', 'Males 15-24')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Males 50+', 'Females 15-24')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})
    R.covout['condcas'][('Females 25-49', 'Males 25-49')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'SBCC & Condom':(0.45,0.55)})

    # HIV testing
    R.covout['hivtest']['FSW'].addccopar({'intercept': (0.15,0.25), 
                                          't': 2016.0,
                                          'FSW programs':(0.85,0.95)})
                                            
    R.covout['hivtest']['Females 0-14'].addccopar({'intercept': (0.05,0.1),
                                          't': 2016.0,
                                          'HTC': (0.85,0.9)})
                                          
    R.covout['hivtest']['Males 0-14'].addccopar({'intercept': (0.05,0.1),
                                          't': 2016.0,
                                          'HTC': (0.85,0.9)})
                                          
    R.covout['hivtest']['Males 15-24'].addccopar({'intercept': (0.05,0.1),
                                              't': 2016.0,
                                              'HTC': (0.65,0.75)})
                                              
    R.covout['hivtest']['Females 25-49'].addccopar({'intercept': (0.15,0.2),
                                              't': 2016.0,
                                              'HTC': (0.65,0.75)})
                                              
    R.covout['hivtest']['Males 25-49'].addccopar({'intercept': (0.05,0.1),
                                              't': 2016.0,
                                              'HTC': (0.65,0.75)})
                                              
    R.covout['hivtest']['Females 15-24'].addccopar({'intercept': (0.15,0.2),
                                              't': 2016.0,
                                              'HTC': (0.85,0.95)})
                                              
    R.covout['hivtest']['Clients'].addccopar({'intercept': (0.1,0.15),
                                              't': 2016.0,
                                              'HTC': (0.85,0.95)})

    R.covout['hivtest']['MSM'].addccopar({'intercept': (0.15,0.25),
                                          't': 2016.0, 
                                          'MSM programs': (0.85,0.95)})

    R.covout['hivtest']['Females 50+'].addccopar({'intercept': (0.15,0.2), 
                                            't': 2016.0,
                                             'HTC': (0.75,0.85)})

    R.covout['hivtest']['Males 50+'].addccopar({'intercept': (0.05,0.1),
                                            't': 2016.0,
                                              'HTC': (0.65,0.75)})


## Compare epidemic projections under calibration vs cost fns
if 'compareepi' in tests:
    
    from optima import Parscen, Budgetscen

    ## Define scenarios
    scenlist = [
        Parscen(name='Current conditions',
                parsetname='default',
                pars=[]),

        Budgetscen(name='Current budget',
              parsetname='default',
              progsetname='Default Program Set',
              t=2016,
              budget=R.getdefaultbudget())]

    P.addscenlist(scenlist)
    P.runscenarios() 
     
    if doplot:
        from optima import pygui
        pygui(P.results[-1], toplot='default')
    

    done(t)



## Compare parameter values
if 'compareoutcomes' in tests:
    comparison = R.compareoutcomes(parset=P.parsets[0], year=2016, doprint=True)
    done(t)


## Same
if 'savezambia' in tests:


    from optima import saveobj
    newfilename = 'exercise_complete-1-costfns.prj'

    saveobj(newfilename, P)



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)    
    
