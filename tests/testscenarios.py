"""
Test scenarios

Version: 2016jan27
"""


## Define tests to run here!!!
tests = [
#'standardscen',
#'maxbudget',
#'90-90-90'
'VMMC'
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


## Standard scenario test
if 'standardscen' in tests:
    t = tic()

    print('Running standard scenarios test...')
    from optima import Parscen, Budgetscen, Coveragescen
    from optima.defaults import defaultproject
    from numpy import array
    
    P = defaultproject('concentrated')
    pops = P.data['pops']['short']
    malelist = [i for i in range(len(pops)) if P.data['pops']['male'][i]]
    
    caspships = P.parsets['default'].pars[0]['condcas'].y.keys()
    
    ## Define scenarios
    scenlist = [
        Parscen(name='Current conditions',
                parsetname='default',
                pars=[]),

        Parscen(name='Get lots of people on treatment',
             parsetname='default',
             pars=[{'endval': 100000.,
                'endyear': 2020,
                'name': 'numtx',
                'for': 'tot',
                'startval': 3350.,
                'startyear': 2015}]),

        Parscen(name='Imagine that no-one gets circumcised',
             parsetname='default',
             pars=[{'endval': 0.,
                'endyear': 2020,
                'name': 'circum',
                'for': malelist,
                'startval': .97,
                'startyear': 2015}]),

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
              t=2016,
              budget={'Condoms': 1e7,
                           'FSW programs': 1e6,
                           'HTC':2e7,
                           'OST':1e6,
                           'ART':1e6}),

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
    P.scens[2].active = True # Turn off another scenario
    
    # Turn off budget scenarios
    for i,scen in P.scens.items():
        if isinstance(scen, (Budgetscen, Coveragescen)):
            P.scens[i].active = False
    
    # Run the scenarios
    P.runscenarios() 
     
    if doplot:
        from optima import pygui
        pygui(P.results[-1], toplot='default')

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
            output += 'Number treated: %s\n' % (P.results[-1].raw[scenno][0]['people'][settings.alltx,:,findinds(tvec,yr)].sum(axis=(0,1)))
            output += 'Prop treated: %s\n' % (P.results[-1].raw[scenno][0]['people'][settings.alltx,:,findinds(tvec,yr)].sum(axis=(0,1))/P.results[-1].raw[scenno][0]['people'][settings.allplhiv,:,findinds(tvec,yr)].sum(axis=(0,1)))
            print output


    done(t)



## 90-90-90 scenario test
if '90-90-90' in tests:
    t = tic()

    print('Running standard scenarios test...')
    from optima import Parscen, defaults, pygui, plotpeople
    
    P = defaults.defaultproject('simple')
    P.settings.usecascade = True
    P.runsim()
    
    pops = P.data['pops']['short']

    ## Define scenarios
    scenlist = [
        Parscen(name='Current conditions',
                parsetname='default',
                pars=[]),

         Parscen(name='90-90-90',
              parsetname='default',
              pars=[
              {'name': 'propdx',
              'for': ['tot'],
              'startyear': 2016,
              'endyear': 2020,
              'startval': .5,
              'endval': .9,
              },
              
              {'name': 'propcare',
              'for': ['tot'],
              'startyear': 2016,
              'endyear': 2020,
              'startval': .5,
              'endval': .9,
              },
              
              {'name': 'proptx',
              'for': ['tot'],
              'startyear': 2016,
              'endyear': 2020,
              'startval': .5,
              'endval': .9,
              },
              
              {'name': 'treatvs',
              'for': ['tot'],
              'startyear': 2016,
              'endyear': 2020,
              'startval': .5,
              'endval': .9,
              },
                ]),
        ]

    # Store these in the project
    P.addscenlist(scenlist)
    
    # Run the scenarios
    P.runscenarios() 
     
    if doplot:
        ppl = P.results[-1].raw['90-90-90'][0]['people']
        plotpeople(P, ppl)
        pygui(P.results[-1], toplot='cascade')

    done(t)




## Set up project etc.
if 'maxbudget' in tests:
    t = tic()

    print('Running maximum budget scenario test...')
    from optima import Budgetscen, odict
    from optima import defaults
    
    ## Set up default project
    P = defaults.defaultproject('generalized')
    
    ## Define scenarios
    scenlist = [
        Budgetscen(name='Current conditions', parsetname='default', progsetname='default', t=[2016], budget=P.progsets['default'].getdefaultbudget()),
        Budgetscen(name='Unlimited spending', parsetname='default', progsetname='default', t=[2016], budget=odict([(key, 1e9) for key in P.progsets['default'].programs.keys()])),
        ]
    
    # Run the scenarios
    P.addscenlist(scenlist)
    P.runscenarios() 
     
    if doplot:
        from optima import pygui
        pygui(P.results[-1], toplot='default')



## Set up project etc.
if 'VMMC' in tests:
    t = tic()

    print('Running VMMC scenario test...')
    from optima import Parscen, Budgetscen
    from optima import defaults
    
    P = defaults.defaultproject('generalized')
    pops = P.data['pops']['short']

    malelist = [i for i in range(len(pops)) if P.data['pops']['male'][i]]
    caspships = P.parsets['default'].pars[0]['condcas'].y.keys()
    
    ## Define scenarios
    scenlist = [
        Parscen(name='Current conditions',
                parsetname='default',
                pars=[]),

        Parscen(name='Imagine that no-one gets circumcised',
             parsetname='default',
             pars=[{'endval': 0.,
                'endyear': 2020,
                'name': 'circum',
                'for': malelist,
                'startval': .85,
                'startyear': 2015}]),

         Budgetscen(name='Scale up VMMC program',
              parsetname='default',
              progsetname='default',
              t=2016,
              budget={'Condoms': 1e7,
                      'VMMC': 1e6,
                      'FSW programs': 1e6,
                      'HTC':2e7,
                      'PMTCT':1e6,
                      'ART':1e6}),

        ]
    
    # Store these in the project
    P.addscenlist(scenlist)
    
    # Run the scenarios
    P.runscenarios()
     
    if doplot:
        from optima import pygui, plotpeople
        pygui(P.results[-1], toplot='default')

    done(t)
