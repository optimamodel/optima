"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016jan18 by cliffk
"""


## Define tests to run here!!!
tests = [
'standardscen',
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


## GUI test
if 'standardscen' in tests:
    t = tic()

    print('Running standard scenarios test...')
    from optima import Project, Parscen, Budgetscen, Coveragescen
    from optima.defaults import defaultprogset
    from numpy import array
    
    # Make project and store results from default sim
    P = Project(spreadsheet='testpwid.xlsx')
    results = P.runsim('default')

    caspships = P.parsets['default'].pars[0]['condcas'].y.keys()

    # Get a default progset 
    R = defaultprogset(P, addpars=True, addcostcov=True, filterprograms=['Condoms', 'FSW programs', 'HTC', 'ART', 'OST'])
    
    # Modify target pars and pops
    R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'M 0-14'})
    R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'F 0-14'})
    R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('M 0-14'))
    R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('F 0-14'))
    R.updateprogset()

    # Add program effects
    R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
    R.covout['condcas'][('FSW', 'Clients')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
    R.covout['condcas'][('Clients', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 15+','Clients')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65), 'MSM programs':(0.75,0.85)})
    R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
    R.covout['condcas'][('FSW', 'M 15+')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW programs':(0.55,0.65)})
    R.covout['condcas'][('M 15+', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 15+', 'M 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('F 15+', 'PWID')].addccopar({'intercept': (0.1,0.2), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('PWID', 'F 15+')].addccopar({'intercept': (0.1,0.2), 't': 2016.0, 'Condoms':(0.35,0.45)})

    R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW programs':(0.9,0.95)})
    R.covout['condcom'][('FSW', 'Clients')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW programs':(0.9,0.95)})

    R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99), 'FSW programs':(0.95,0.99)})
    R.covout['hivtest']['MSM'].addccopar({'intercept': (0.05,0.1), 't': 2016.0, 'HTC': (0.95,0.99), 'MSM programs':(0.95,0.99)})
    R.covout['hivtest']['Clients'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['M 15+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['F 15+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['PWID'].addccopar({'intercept': (0.05,0.1), 't': 2016.0, 'HTC': (0.95,0.99)})

    R.covout['numtx']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
    R.covout['numost']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
    
    # Store this program set in the project
    P.addprogset(R)
    
    ## Define scenarios
    scenlist = [
        Parscen(name='Current conditions',
                parsetname='default',
                pars=[]),

        Parscen(name='Full casual condom use',
             parsetname='default',
             pars=[{'endval': 1.,
                'endyear': 2015,
                'name': 'condcas',
                'for': caspships,
                'startval': 1.,
                'startyear': 2005}]),

         Parscen(name='More casual acts',
              parsetname='default',
              pars=[{'endval': 100.,
                'endyear': 2015,
                'name': 'actscas',
                'for': caspships,
                'startval': 100.,
                'startyear': 2005}]),

         Parscen(name='100% testing',
              parsetname='default',
              pars=[{'endval': 1.,
                'endyear': 2020,
                'name': 'hivtest',
                'for': ['FSW', 'Clients', 'MSM', 'M 15+', 'F 15+'],
                'startval': .5,
                'startyear': 2016}]),

         Parscen(name='Increased STI prevalence in FSW',
              parsetname='default',
              pars=[{'endval': 0.8,
                'endyear': 2015,
                'name': 'stiprev',
                'for': 0,
                'startval': 0.8,
                'startyear': 2005}]),

         Parscen(name='Get 50K people on OST',
              parsetname='default',
              pars=[{'endval': 50000,
                'endyear': 2015,
                'name': 'numost',
                'for': 0,
                'startval': 1250,
                'startyear': 2005}]),

         Budgetscen(name='Keep current investment in condom program',
              parsetname='default',
              progsetname='default',
              t=[2016,2020],
              budget={'Condoms': array([1e7,1e7]),
                           'FSW programs':array([1e6,1e6]),
                           'HTC':array([2e7,2e7]),
                           'OST':array([1e6,1e6]),
                           'ART':array([1e6,1e6])}),

         Budgetscen(name='Double investment in condom program',
              parsetname='default',
              progsetname='default',
              t=[2016,2020],
              budget={'Condoms': array([1e7,2e7]),
                           'FSW programs':array([1e6,1e6]),
                           'HTC':array([2e7,2e7]),
                           'OST':array([1e6,1e6]),
                           'ART':array([1e6,1e6])}),

         Coveragescen(name='A million people covered by the condom program',
              parsetname='default',
              progsetname='default',
              t=[2016,2020],
              coverage={'Condoms': array([285706.,1e6]),
                           'FSW programs':array([15352.,15352.]),
                           'HTC':array([1332862.,1332862.]),
                           'OST':array([1250.,1250.]),
                           'ART':array([3324.,3324.])}),

         Budgetscen(name='Double investment in ART, HTC and OST',
              parsetname='default',
              progsetname='default',
              t=[2016,2018,2020],
              budget={'Condoms': array([1e7,1e7,1e7]),
                           'FSW programs':array([1e6,1e6,1e6]),
                           'HTC':array([2e7,3e7,4e7]),
                           'OST':array([1e6,1.5e6,2e6]),
                           'ART':array([1e6,1.5e6,2e6])})
        ]
    
    # Store these in the project
    P.addscenlist(scenlist)
    P.scens['A million people covered by the condom program'].active = False # Turn off a scenario
    P.scens[2].active = False # Turn off another scenario
    
    # Run the scenarios
    P.runscenarios() 
     
    if doplot:
        from optima import pygui, plotallocs
        pygui(P.results[-1])
        plotallocs(P.results[-1])

    if showstats:
        from optima import Settings, findinds
        from numpy import arange
        settings = Settings()
        tvec = arange(settings.start,settings.end+settings.dt,settings.dt)
        yr = 2020
        blank()
        for scenno, scen in enumerate([scen for scen in P.scens.values() if scen.active]):
            output = '===================================\n'
            output += scen.name
            output += '\n'           
            output += 'PLHIV: %s\n' % (P.results[-1].raw[scenno][0]['people'][settings.allplhiv,:,findinds(tvec,yr)].sum(axis=(0,1)))
            output += 'Prop aware: %s\n' % (P.results[-1].raw[scenno][0]['people'][settings.alldx,:,findinds(tvec,yr)].sum(axis=(0,1))/P.results[-1].raw[scenno][0]['people'][settings.allplhiv,:,findinds(tvec,yr)].sum(axis=(0,1)))
            output += 'Number treated: %s\n' % (P.results[-1].raw[scenno][0]['people'][settings.alltreat,:,findinds(tvec,yr)].sum(axis=(0,1)))
            output += 'Prop treated: %s\n' % (P.results[-1].raw[scenno][0]['people'][settings.alltreat,:,findinds(tvec,yr)].sum(axis=(0,1))/P.results[-1].raw[scenno][0]['people'][settings.allplhiv,:,findinds(tvec,yr)].sum(axis=(0,1)))
            print output


    done(t)