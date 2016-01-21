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
    from optima import Project
    from optima.defaults import defaultprogset
    from numpy import array
    
    P = Project(spreadsheet='test7pops.xlsx')
    caspships = P.data['pships']['cas']

    R = defaultprogset(P, addpars=True, addcostcov=True, filterprograms=['Condoms', 'FSW_programs', 'HTC', 'ART'])

    R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'M 0-14'})
    R.programs['HTC'].rmtargetpar({'param': 'hivtest', 'pop': 'F 0-14'})
    R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('M 0-14'))
    R.programs['HTC'].targetpops.pop(R.programs['HTC'].targetpops.index('F 0-14'))
    R.updateprogset()

    R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
    R.covout['condcas'][('Clients', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65), 'MSM_programs':(0.75,0.85)})
    R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
    R.covout['condcas'][('M 15+', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW_programs':(0.9,0.95)})
    R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99), 'FSW_programs':(0.95,0.99)})
    R.covout['hivtest']['MSM'].addccopar({'intercept': (0.05,0.1), 't': 2016.0, 'HTC': (0.95,0.99), 'MSM_programs':(0.95,0.99)})
    R.covout['hivtest']['Clients'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['M 15+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['hivtest']['F 15+'].addccopar({'intercept': (0.15,0.2), 't': 2016.0, 'HTC': (0.95,0.99)})
    R.covout['numtx']['tot'].addccopar({'intercept': (100.0,150.0), 't': 2016.0})
    
    ## Define scenarios
    scenlist = [
        {'name': 'Current conditions',
                 'parset': P.parsets['default'],
                 'scenariotype': 'parameter',
                 'pars': []},
        {'name': 'Full casual condom use',
         'parset': P.parsets['default'],
         'scenariotype': 'parameter',
         'pars': [{'endval': 1.,
            'endyear': 2015,
            'name': 'condcas',
            'for': caspships,
            'startval': 1.,
            'startyear': 2005}]},
         {'name': 'More casual acts',
          'parset': P.parsets['default'],
          'scenariotype': 'parameter',
          'pars': [{'endval': 100.,
            'endyear': 2015,
            'name': 'actscas',
            'for': caspships,
            'startval': 100.,
            'startyear': 2005}]},
         {'name': '100% testing',
          'parset': P.parsets['default'],
          'scenariotype': 'parameter',
          'pars': [{'endval': 1.,
            'endyear': 2020,
            'name': 'hivtest',
            'for': ['FSW', 'Clients', 'MSM', 'M 15+', 'F 15+'],
            'startval': .5,
            'startyear': 2016}]},
         {'name': 'Increased STI prevalence in FSW',
          'parset': P.parsets['default'],
          'scenariotype': 'parameter',
          'pars': [{'endval': 0.8,
            'endyear': 2015,
            'name': 'stiprev',
            'for': 0,
            'startval': 0.8,
            'startyear': 2005}]},
         {'name': 'Keep current investment in condom program',
          'parset': P.parsets['default'],
          'scenariotype': 'program',
          'progscenariotype': 'budget',
          'progset': R,
          't': [2016,2020],
          'programs': {'Condoms': array([1e7,1e7]),
                       'FSW_programs':array([1e6,1e6]),
                       'HTC':array([2e7,2e7]),
                       'ART':array([1e6,1e6])}},
         {'name': 'Double investment in condom program',
          'parset': P.parsets['default'],
          'scenariotype': 'program',
          'progscenariotype': 'budget',
          'progset': R,
          't': [2016,2020],
          'programs': {'Condoms': array([1e7,2e7]),
                       'FSW_programs':array([1e6,1e6]),
                       'HTC':array([2e7,2e7]),
                       'ART':array([1e6,1e6])}},
         {'name': 'A million people covered by the condom program',
          'parset': P.parsets['default'],
          'scenariotype': 'program',
          'progscenariotype': 'coverage',
          'progset': R,
          't': [2016,2020],
          'programs': {'Condoms': array([285706.,1e6]),
                       'FSW_programs':array([15352.,15352.]),
                       'HTC':array([1332862.,1332862.]),
                       'ART':array([3324.,3324.])}},
         {'name': 'Double investment in ART and HTC',
          'parset': P.parsets['default'],
          'scenariotype': 'program',
          'progscenariotype': 'budget',
          'progset': R,
          't': [2016,2020],
          'programs': {'Condoms': array([1e7,1e7]),
                       'FSW_programs':array([1e6,1e6]),
                       'HTC':array([2e7,4e7]),
                       'ART':array([1e6,2e6])}}
        ]
    
    from optima import runscenarios
    allresults = runscenarios(scenlist=scenlist)
     
    if doplot:
        from optima.plotpeople import plotpeople
        plotpeople(allresults)

    if showstats:
        from optima import Settings, findinds
        from numpy import arange
        settings = Settings()
        tvec = arange(settings.start,settings.end+settings.dt,settings.dt)
        yr = 2020
        blank()
        for scenno, scen in enumerate(scenlist):
            output = '===================================\n'
            output += scen['name']
            output += '\n'           
            output += 'PLHIV: %s\n' % (allresults[scenno].raw[0]['people'][settings.allplhiv,:,findinds(tvec,yr)].sum(axis=(0,1)))
            output += 'Prop aware: %s\n' % (allresults[scenno].raw[0]['people'][settings.alldx,:,findinds(tvec,yr)].sum(axis=(0,1))/allresults[scenno].raw[0]['people'][settings.allplhiv,:,findinds(tvec,yr)].sum(axis=(0,1)))
            output += 'Number treated: %s\n' % (allresults[scenno].raw[0]['people'][settings.alltreat,:,findinds(tvec,yr)].sum(axis=(0,1)))
            output += 'Prop treated: %s\n' % (allresults[scenno].raw[0]['people'][settings.alltreat,:,findinds(tvec,yr)].sum(axis=(0,1))/allresults[scenno].raw[0]['people'][settings.allplhiv,:,findinds(tvec,yr)].sum(axis=(0,1)))
            
            print output


    done(t)