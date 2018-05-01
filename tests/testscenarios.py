"""
Test scenarios

Version: 2016feb07
"""


## Define tests to run here!!!
tests = [
'standardscen',
#'maxcoverage',
'budget',
#'90-90-90',
#'sensitivity',
#'VMMC'
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
    from optima import Parscen, Budgetscen, Coveragescen, defaultproject, setparscenvalues
    from numpy import array
    
    P = defaultproject('concentrated')
    pops = P.data['pops']['short']
    malelist = [i for i in range(len(pops)) if P.data['pops']['male'][i]]
    
    caspships = P.parsets['default'].pars['condcas'].y.keys()
    
    # Example of generating a dict to autofill parameter scenarios    
    thisdict = setparscenvalues(parset=P.parsets[0], parname='hivtest', forwhom='FSW',startyear=2016.)
    thisdict = setparscenvalues(parset=P.parsets[0], parname='proptx', forwhom='tot')
    

    ## Create scenarios
    scenlist = [
        Parscen(name='Get lots of people on treatment',
                parsetname=0,
                pars=[{
                 'name': 'numtx',
                 'for': 'tot',
                 'startyear': 2016.,
                 }]),

        Parscen(name='Imagine that no-one gets circumcised',
             parsetname='default',
             pars=[{
                 'name': 'propcirc',
                 'for': P.pars()['propcirc'].keys(),
                 'startyear': 2015,
                 'endyear': 2020,
                 'endval': 0.,
                 }]),

        Parscen(name='Increase numpmtct',
             parsetname='default',
             pars=[{
                 'name': 'numpmtct',
                 'for': 'tot',
                 'startyear': 2015.,
                 'endyear': 2020,
                 'endval': 0.9,
                 }]),

        Parscen(name='Full casual condom use',
             parsetname='default',
             pars=[{
                 'name': 'condcas',
                 'for': caspships,
                 'startyear': 2005,
                 'endyear': 2015,
                 'endval': 1.,
                 }]),

         Parscen(name='More casual acts',
              parsetname='default',
              pars=[{
                  'name': 'actscas',
                  'for': caspships,
                  'startyear': 2005,
                  'endyear': 2015,
                  'endval': 2.,
                  }]),

         Parscen(name='100% testing',
              parsetname='default',
              pars=[{
                  'name': 'hivtest',
                  'for': ['FSW', 'Clients', 'MSM', 'M 15+', 'F 15+'],
                  'startyear': 2000.,
                  'endyear': 2020,
                  'endval': 1.,
                  }]),

         Parscen(name='Increased STI prevalence in FSW',
              parsetname='default',
              pars=[{
                  'name': 'stiprev',
                  'for': 0,
                  'startyear': 2005.,
                  'endyear': 2015,
                  'endval': 0.8,
                  }]),

         Parscen(name='Get 50K people on OST',
              parsetname='default',
              pars=[{
                  'name': 'numost',
                  'for': 0,
                  'startyear': 2005.,
                  'endyear': 2015,
                  'endval': 50000,
                  }]),

         Budgetscen(name='Keep current investment in condom program',
              parsetname='default',
              progsetname='default',
              t=2016,
              budget={'Condoms': 1e7,
                           'FSW programs': 1e6,
                           'HTC':2e7,
                           'ART':1e6}),

         Budgetscen(name='Double investment in condom program',
              parsetname='default',
              progsetname='default',
              t=[2016,2020],
              budget={'Condoms': array([1e7,2e7]),
                           'FSW programs':array([1e6,1e6]),
                           'HTC':array([2e7,2e7]),
                           'ART':array([1e6,1e6])}),

         Coveragescen(name='A million people covered by the condom program',
              parsetname='default',
              progsetname='default',
              t=[2016,2020],
              coverage={'Condoms': array([285706.,1e6]),
                           'FSW programs':array([15352.,15352.]),
                           'HTC':array([1332862.,1332862.]),
                           'ART':array([3324.,3324.])}),

         Budgetscen(name='Double investment in ART, HTC and OST',
              parsetname='default',
              progsetname='default',
              t=[2016,2018,2020],
              budget={'Condoms': array([1e7,1e7,1e7]),
                           'FSW programs':array([1e6,1e6,1e6]),
                           'HTC':array([2e7,3e7,4e7]),
                           'ART':array([1e6,1.5e6,2e6])}),

         Budgetscen(name='Test some progs only',
              parsetname='default',
              progsetname='default',
              t=2016,
              budget={'Condoms': 1e7,
                           'ART':1e6})

        ]
    
    # Store these in the project
    P.addscens(scenlist, overwrite=True)

    # Run the scenarios
    P.runscenarios() 
     
    if doplot:
        from optima import pygui
        pygui(P.results[-1], toplot='default')

    done(t)


## Test scenario sensitivity feature
if 'sensitivity' in tests:
    t = tic()

    print('Testing scenario sensitivity...')
    from optima import Parscen, defaultproject, pygui, findinds
    from numpy import array
    
    P = defaultproject('best')
    P.cleanresults() 
    P.pars()['fixproptx'].t = 2100 # WARNING, kludgy
    
    ## Define scenarios
    scenlist = [
        Parscen(name='Current conditions',
                parsetname='default',
                pars=[]),

        Parscen(name='Increase numtx',
              parsetname='default',
              pars=[
              {'name': 'numtx',
              'for': 'tot',
              'startyear': 2014.,
              'endyear': 2020.,
              'endval': 68000.,
              }]),
        ]
        
    # Store these in the project
    P.addscens(scenlist, overwrite=True)
    # Run the scenarios
    P.runscenarios(debug=True,nruns=5,tosample='force') 
    
    resultsdiff = P.result().diff(base=1)
    
#    output = '\n\n----------------\nScenario impact:\n'
#    output += 'Infections averted: %s [%s, %s]\n' % (resultsdiff.get('numinci', key='Current conditions', year='all')[0,17:].sum(), resultsdiff.get('numinci', key='Current conditions', year='all')[1,17:].sum(), resultsdiff.get('numinci', key='Current conditions', year='all')[2,17:].sum())
#    output += 'Deaths averted: %s [%s, %s]\n' % (resultsdiff.get('numdeath', key='Current conditions', year='all')[0,17:].sum(), resultsdiff.get('numdeath', key='Current conditions', year='all')[1,17:].sum(), resultsdiff.get('numdeath', key='Current conditions', year='all')[2,17:].sum())
#    output += 'DALYs averted: %s [%s, %s]\n' % (resultsdiff.get('numdaly', key='Current conditions', year='all')[0,17:].sum(), resultsdiff.get('numdaly', key='Current conditions', year='all')[1,17:].sum(), resultsdiff.get('numdaly', key='Current conditions', year='all')[2,17:].sum())
#    print output

    done(t)

    


## 90-90-90 scenario test
if '90-90-90' in tests:
    t = tic()

    print('Running standard scenarios test...')
    from optima import Parscen, defaultproject, pygui
    
    P = defaultproject('best')
    P.cleanresults() # Check that scenarios can be run even if no results stored
    P.parset().fixprops(False) # To ensure the scenarios have an effect
    
    pops = P.data['pops']['short']
    
    startyear = 2015.
    endyear = 2020.
    
    ## Define scenarios
    scenlist = [
        Parscen(name='Current conditions',
                parsetname='default',
                pars=[]),

         Parscen(name='90-90-90',
              parsetname='default',
              pars=[
              {'name': 'propdx',
              'for': 'tot',
              'startyear': startyear,
              'endyear': endyear,
              'endval': .9,
              },
              
              {'name': 'propcare',
              'for': 'tot',
              'startyear': startyear,
              'endyear': endyear,
              'endval': .9,
              },
              
              {'name': 'proptx',
              'for': 'tot',
              'startyear': startyear,
              'endyear': endyear,
              'endval': .9,
              },
              
              {'name': 'propsupp',
              'for': 'tot',
              'startyear': startyear,
              'endyear': endyear,
              'endval': .9,
              },
                ]),
                
         Parscen(name='Increase numtx',
              parsetname='default',
              pars=[
              {'name': 'numtx',
              'for': 'tot',
              'startyear': startyear,
              'endyear': 2020.,
              'endval': 68000.,
              }]),
                                
        ]

    # Store these in the project
    P.addscens(scenlist, overwrite=True)
    P.scens[2].active = False # Turn off 90-90-90 scenario

    # Run the scenarios
    P.runscenarios(debug=True) 

  
     
    if doplot:
#        ppl = P.results[-1].raw['90-90-90'][0]['people']
#        plotpeople(P, ppl)
        pygui(P.results[-1], toplot='default')

    P.result().summary()

    done(t)





#################################################################################################################
## Coverage
#################################################################################################################

if 'maxcoverage' in tests:
    t = tic()

    print('Running maximum coverage scenario test...')
    from optima import Coveragescen, Parscen, defaultproject, dcp
    from numpy import array
    
    ## Set up default project
    P = defaultproject('best')
    
    ## Define scenarios
    defaultbudget = P.progsets['default'].getdefaultbudget()
    maxcoverage = dcp(defaultbudget) # It's just an odict, though I know this looks awful
    for key in maxcoverage: maxcoverage[key] = array([maxcoverage[key]+1e9])
    scenlist = [
        Parscen(name='Current conditions', parsetname='default', pars=[]),
        Coveragescen(name='Full coverage', parsetname='default', progsetname='default', t=[2016], coverage=maxcoverage),
        ]
    
    # Run the scenarios
    P.addscens(scenlist, overwrite=True)
    P.runscenarios() 
     
    if doplot:
        from optima import pygui
        pygui(P.results[-1], toplot='default')




## Test budget scenarios
if 'budget' in tests:
    t = tic()

    print('Running budget scenario test...')
    from optima import Budgetscen, defaultproject, dcp
    from numpy import array
    
    ## Set up default project
    P = defaultproject('best',dorun=False)
    
    ## Define scenarios
    defaultbudget = P.progsets['default'].getdefaultbudget()
    maxbudget = dcp(defaultbudget)
    for key in maxbudget: maxbudget[key] += 1e14
    zerobudget = dcp(defaultbudget)
    for key in zerobudget: zerobudget[key] = array([0.]) # Alternate way of setting to zero   
    scenlist = [
        Budgetscen(name='Current conditions', parsetname='default', progsetname='default', t=[2016], budget=defaultbudget),
        Budgetscen(name='Unlimited spending', parsetname='default', progsetname='default', t=[2016], budget=maxbudget),
        Budgetscen(name='Zero spending', parsetname='default', progsetname='default', t=[2016], budget=zerobudget),
        ]
    
    # Run the scenarios
    P.addscens(scenlist)
    P.runscenarios(nruns=1,tosample='force',ccsample='rand',verbose=3, base=2) 
    
    P.result().export()
     
    if doplot:
        from optima import pygui
        pygui(P.results[-1], toplot='default')





## Set up project etc.
if 'VMMC' in tests:
    t = tic()

    print('Running VMMC scenario test...')
    from optima import Parscen, Budgetscen, defaultproject
    
    P = defaultproject('generalized',dorun=False)
#    P.runsim()
    pops = P.data['pops']['short']

    malelist = findinds(P.data['pops']['male'])
    femalelist = findinds(P.data['pops']['female'])
    caspships = P.parsets['default'].pars['condcas'].y.keys()
    
    ## Define scenarios
    scenlist = [
        Parscen(name='Current conditions',
                parsetname='default',
                pars=[]),

        Parscen(name='Proportion circumcised',
             parsetname='default',
             pars=[{'endval': 0.2,
                'endyear': 2020,
                'name': 'propcirc',
                'for': femalelist,
                'startval': .85,
                'startyear': 2015.2}]),
        
#        Budgetscen(name='Default budget',
#              parsetname='default',
#              progsetname='default',
#              t=2015,
#              budget=P.progsets['default'].getdefaultbudget()),
#
#         Budgetscen(name='Scale up VMMC program',
#              parsetname='default',
#              progsetname='default',
#              t=2016,
#              budget={'VMMC': 1e8}),

        ]
    
    # Store these in the project
    P.addscens(scenlist, overwrite=True)
    
    # Run the scenarios
    P.runscenarios()
     
    if doplot:
        from optima import pygui
#        apd = plotpars([scen.scenparset.pars for scen in P.scens.values()])
        pygui(P.results[-1])
        

    done(t)
