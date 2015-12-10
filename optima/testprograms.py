"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015nov23 by cliffk
"""



## Define tests to run here!!!
tests = [
'makeprograms',
]


##############################################################################
## Initialization
##############################################################################

from optima import tic, toc, blank, pd, odict # analysis:ignore

def done(t=0):
    print('Done.')
    toc(t)
    blank()
    
blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()

doplot = False


##############################################################################
## The tests
##############################################################################

T = tic()





## Project creation test
if 'makeprograms' in tests:
    t = tic()

    print('Running make programs test...')
    from optima import Project, Program, Programset
    
    P = Project(spreadsheet='test.xlsx')

    # First set up some programs. Programs need to be initialized with a name. Often they will also be initialized with targetpars and targetpops
    HTC = Program(name='HTC',
                  targetpars=[{'param': 'hivtest', 'pop': 'Females 15-49'}],
                  targetpops=['Females 15-49'])

    SBCC = Program(name='SBCC',
                   targetpars=[{'param': 'condomcas', 'pop': 'Females 15-49'},
                               {'param': 'hivtest', 'pop': 'Females 15-49'}],
                   targetpops=['Females 15-49'])
                   
    FSW = Program(name='FSW programs',
                  targetpars=[{'param': 'hivtest', 'pop': 'FSW'},
                              {'param': 'condomcas', 'pop': 'FSW'}],
                  targetpops=['FSW'])

    MGT = Program('MGT')

    ART = Program(name='ART',
                  targetpars=[{'param': 'numtx', 'pop': 'Total'}],
                  targetpops=['Total'])

    # Testing methods of program class
    # 1. Adding a target parameter to a program
    HTC.addtargetpar({'param': 'hivtest', 'pop': 'FSW'})
    HTC.addtargetpar({'param': 'hivtest', 'pop': 'Males 15-49'})
    
    ## NOTE that adding a targeted parameter does NOT automatically add a targeted population! Do this separately, e.g.
    HTC.targetpops.append('Males 15-49')
        
    # 2. Removing a target parameter from a program
    HTC.rmtargetpar({'param': 'hivtest', 'pop': 'FSW'})

    # 3. Add historical cost-coverage data point
    HTC.addcostcovdatum({'t':2013,
                         'cost':1e6,
                         'coverage':3e5})
    HTC.addcostcovdatum({'t':2014,
                         'cost':4e7,
                         'coverage':10e5})
    HTC.addcostcovdatum({'t':2015,
                         'cost':1e7,
                         'coverage':4e5})

    # 4. Overwrite historical cost-coverage data point
    HTC.addcostcovdatum({'t':2013,
                         'cost':2e6,
                         'coverage':3e5},
                         overwrite=True)

    # 5. Remove historical cost-coverage data point - specify year only
    HTC.rmcostcovdatum(2013)

    # 6. Add parameters for defining cost-coverage function.
    HTC.costcovfn.addccopar({'saturation': 0.8,
                             't': 2013.0,
                             'unitcost': 30})
                             
    HTC.costcovfn.addccopar({'t': 2016.0,
                             'unitcost': 30})
                             
    HTC.costcovfn.addccopar({'t': 2017.0,
                             'unitcost': 30})
                             
    SBCC.costcovfn.addccopar({'saturation': 0.4,
                              't': 2013.0,
                              'unitcost': 10})

    # 7. Overwrite parameters for defining cost-coverage function.
    HTC.costcovfn.addccopar({'t': 2016.0,
                             'unitcost': 25},
                             overwrite=True)

    # 8. Remove parameters for defining cost-coverage function.
    HTC.costcovfn.rmccopar(2017)

    # 9. Get parameters for defining cost-coverage function for any given year (even if not explicitly entered).
    HTC.costcovfn.getccopar(2014)

    # 10. Get target population size
    HTC.gettargetpopsize(t=[2013,2015],parset=P.parsets['default'])

    # 11. Evaluate cost-coverage function to get coverage for a given year, spending amount and population size
    from numpy import linspace
    HTC.getcoverage(x=linspace(0,1e6,3),t=[2013,2015,2017],parset=P.parsets['default'],total=False)
    HTC.getbudget(x=linspace(0,1e6,3),t=[2013,2015,2017],parset=P.parsets['default'],proportion=False)

    # NB, if you want to evaluate it for a particular population size, can also do...
    HTC.costcovfn.evaluate(x=[1e6],popsize=[1e5],t=[2015],toplot=False)

    # 12. Plot cost-coverage function
    if doplot: HTC.plotcoverage(t=[2013,2015],parset=P.parsets['default'],xupperlim=1e8)

    print('Running make programs set test...')
    # Different ways to initialise
#    R = Programset(programs={'HTC':HTC,'SBCC':SBCC,'MGT':MGT,'SBCC':SBCC})
    R = Programset()
    R = Programset(programs=[HTC,SBCC,MGT])

    # Testing methods of programset class
    # 1. Adding a program
#    R.addprograms({'ART':ART})
    R.addprograms(ART)

    # 2. Removing a program
    R.rmprogram(ART) # Alternative syntax: R.rmprogram('ART')
    
    # 3. See which programs are optimizable
    R.optimizable()

    # 4. Produce a dictionary whose keys are populations targeted by some 
    #    program, and values are the programs that target them
    R.progs_by_targetpop()

    # 5. Produce a dictionary whose keys are paramter types targeted by some 
    #    program, and values are the programs that target them
    R.progs_by_targetpartype()

    # 6. Produce a dictionary whose keys are paramter types targeted by some 
    #    program, and values are dictionaries  whose keys are populations 
    #    targeted by some program, and values are the programs that target them
    R.progs_by_targetpar()

    # 7. Get a vector of coverage levels corresponding to a vector of program allocations
    from numpy import array
    budget={'HTC':array([1e7,1.2e7,1.5e7]),
            'SBCC':array([1e6,1.2e6,1.5e6]),
            'MGT':array([2e5,3e5,3e5])}
            
    coverage={'HTC': array([ 368122.94593941, 467584.47194668, 581136.7363055 ]),
              'MGT': None,
              'SBCC': array([ 97615.90198599, 116119.80759447, 143846.76414342])}
            
    R.getprogcoverage(budget=budget,
                      t=[2015,2016,2020],
                      parset=P.parsets['default'])
                        
    R.getprogbudget(coverage=coverage,
                      t=[2015,2016,2020],
                      parset=P.parsets['default'])
                        
    R.getpopcoverage(budget=budget,
                     t=[2015,2016,2020],
                     parset=P.parsets['default'])

    # 8. Add parameters for defining coverage-outcome function.
    R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.3,
                                                    't': 2013.0,
                                                    'HTC': 0.6,
                                                    'SBCC':0.1})
                                                    
    R.covout['hivtest']['Males 15-49'].addccopar({'intercept': 0.3,
                                                  't': 2016.0,
                                                  'HTC': 0.65})
                                                  
    R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.3,
                                                    't': 2015.0,
                                                    'HTC': 0.5,
                                                    'SBCC':0.15})
                                                    
    R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.4,
                                                    't': 2017.0,
                                                    'HTC': 0.4,
                                                    'SBCC':0.2})

    R.covout['condomcas']['Females 15-49'].addccopar({'intercept': 0.3,
                                                    't': 2015.0,
                                                    'SBCC':0.15})
                                                    
    # 9. Overwrite parameters for defining coverage-outcome function.
    R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.35,
                                                    't': 2015.0,
                                                    'HTC': 0.45,
                                                    'SBCC':0.15},
                                                    overwrite=True)

    # 10. Remove parameters for defining coverage-outcome function.
    R.covout['hivtest']['Females 15-49'].rmccopar(2017)
    
    # 11. Get parameters for defining cost-coverage function for any given year (even if not explicitly entered).
    R.covout['hivtest']['Females 15-49'].getccopar(2014)

    # 12. Get a dictionary of only the program-affected parameters corresponding to a dictionary of program allocations or coverage levels
    outcomes_budget = R.getoutcomes(forwhat=budget,
                                t=[2015,2016,2020],
                                parset=P.parsets['default'],
                                forwhattype='budget')
    outcomes_coverage = R.getoutcomes(forwhat=coverage,
                                t=[2015,2016,2020],
                                parset=P.parsets['default'],
                                forwhattype='coverage')

    # 13. Get a parset of the ALL parameter values corresponding to a vector of program allocations
    progparset1 = R.getparset(forwhat=budget,
                  t=[2015,2016,2020],
                  parset=P.parsets['default'],
                  interaction='random',
                  newparsetname='progparset1',
                  forwhattype='budget')

    # 14. Plot cost-coverage curves for all programs
    if doplot: R.plotallcoverage(t=[2013,2015],
                      parset=P.parsets['default'],
                      xupperlim=1e8)

    # 15. Example use of program scenarios
    if doplot:
        P.parsets['progparset1'] = progparset1
        results0 = P.runsim('default')
        results1 = P.runsim('progparset1')
        from plotpeople import plotpeople
        plotpeople([results0, results1])

    done(t)


print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)