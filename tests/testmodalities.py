"""
Test script for service modalities

Details:
Three different programs are targeting testing rates for F 15-49.
This script demonstrates the effect of these programs under different interaction assumptions.
It can also be used as a test script, to ensure that the calculations are being done correctly.

Version: 2016jan05 by cliffk
"""


## Define tests to run here!!!
tests = [
'modalities',
'scaleup',
'costcov'
]

##############################################################################
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd, odict, demo # analysis:ignore

if 'doplot' not in locals(): doplot = True
if 'showstats' not in locals(): showstats = True

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



## modalities test
if 'modalities' in tests:
    t = tic()

    print('Testing service modalities...')
    from optima import Project, Program, Programset, dcp
    from numpy import array
    from numpy.testing import assert_allclose
    # Uncomment the line below to disable the assert statements and run through to completion
    #assert_allclose = lambda x,y: True
    
    P = Project(spreadsheet='simple.xlsx')
    
    eps = 1e-2
    atol = 1e-2
    testval_HTC_clinics_cov = 0.244944433098 # 0.42475173
    testval_HTC_outreach_cov = 0.0227951129721  # 0.43792895
    testval_HTC_hometest_cov = 0.0566322089804 #0.44181250

    testval_nested =  0.42475173
    testval_random = 0.43792895
    testval_additive = 0.44181250
    
    # First set up some programs
    HTC_clinics = Program(short='HTC_clinics',
                  targetpars=[{'param': 'hivtest', 'pop': 'F 15-49'}],
                  targetpops=['F 15-49'])
    
    HTC_outreach = Program(short='HTC_outreach',
                  targetpars=[{'param': 'hivtest', 'pop': 'F 15-49'}],
                  targetpops=['F 15-49'])
                   
    HTC_hometest = Program(short='HTC_hometest',
                  targetpars=[{'param': 'hivtest', 'pop': 'F 15-49'}],
                  targetpops=['F 15-49'])
    
    # Add cost-coverage function parameters to each program
    HTC_clinics.costcovfn.addccopar({'t': 2013.0,
                                     'saturation': (0.35,0.45),
                                     'unitcost': (35,45)})
                             
    HTC_outreach.costcovfn.addccopar({'t': 2013.0,
                                     'saturation':(0.55,0.65),
                                      'unitcost': (45,55)})
                             
    HTC_hometest.costcovfn.addccopar({'t': 2013.0,
                                     'saturation':(0.35,0.45),
                                      'unitcost': (15,25)})
    
    # Combine the 3 program together in a program set
    R = Programset(programs=[HTC_clinics,HTC_outreach,HTC_hometest])
    
    # Add parameters for the coverage-outcome functions
    R.covout['hivtest']['F 15-49'].addccopar({'intercept': (0.25,0.35),
                                                    't': 2013.0,
                                                    'HTC_clinics': (0.75,0.85),
                                                    'HTC_outreach': (0.85,0.95),
                                                    'HTC_hometest':(0.35,0.45)})
                       
    # Define the budget and the type of interaction
    budget = {'HTC_clinics': array([ 1e7,]),
              'HTC_outreach': array([ 1e6,]),
              'HTC_hometest': array([ 1e6,])}

    # Get the coverage of each program associated with this budget
    coverage = R.getprogcoverage(budget=budget,
                                 t=2013,
                                 parset=P.parsets['default'],
                                 proportion=True)
                                 
    coverage_number = R.getprogcoverage(budget=budget,
                                 t=2013,
                                 parset=P.parsets['default'],
                                 proportion=False)
    
    # Get the outcomes associated with this budget
    R.covout['hivtest']['F 15-49'].interaction = 'nested'
    outcomes_nested = R.getoutcomes(coverage_number,
                                    t=2013,
                                    parset=P.parsets['default'])
    
    R.covout['hivtest']['F 15-49'].interaction = 'random'
    outcomes_random = R.getoutcomes(coverage_number,
                                    t=2013,
                                    parset=P.parsets['default'])
    
    R.covout['hivtest']['F 15-49'].interaction = 'additive'
    outcomes_additive = R.getoutcomes(coverage_number,
                                    t=2013,
                                    parset=P.parsets['default'])
    
#    assert_allclose(outcomes_nested['hivtest']['F 15-49'][0],testval_nested,atol=atol)
#    assert_allclose(outcomes_random['hivtest']['F 15-49'][0],testval_random,atol=atol)
#    assert_allclose(outcomes_additive['hivtest']['F 15-49'][0],testval_additive,atol=atol)
#    
    r1 = 'PASS' if abs(outcomes_nested['hivtest']['F 15-49'][0]-testval_nested)<eps else 'FAIL'
    r2 = 'PASS' if abs(outcomes_random['hivtest']['F 15-49'][0]-testval_random)<eps else 'FAIL'
    r3 = 'PASS' if abs(outcomes_additive['hivtest']['F 15-49'][0]-testval_additive)<eps else 'FAIL'
    
    def summary():
        ''' Print out useful information'''
        output = '\n'
        output += '===================================\n'
        output += 'Calculated outcomes\n'
        output += '   Nested: %s\n'    % outcomes_nested['hivtest']['F 15-49'][0]
        output += '   Random: %s\n'    % outcomes_random['hivtest']['F 15-49'][0]
        output += ' Additive: %s\n'    % outcomes_additive['hivtest']['F 15-49'][0]
        output += '===================================\n'
        output += 'Outcomes should be:\n'
        output += '   Nested: %s\n'    % testval_nested
        output += '   Random: %s\n'    % testval_random
        output += ' Additive: %s\n'    % testval_additive
        output += '===================================\n'
        output += 'Test results:\n'
        output += '   Nested: %s\n' % (r1) 
        output += '   Random: %s\n' % (r2) 
        output += ' Additive: %s\n' % (r3) 
        output += '===================================\n'
        print output
    
    if showstats: summary()
    
    
    
if 'scaleup' in tests:
    # See the effect of scaling up one of the programs
    budget_outreachscaleup = {'HTC_clinics': array([ 1e7,]),
              'HTC_outreach': array([ 1e7,]),
              'HTC_hometest': array([ 1e6,])}
    
    coverage_outreachscaleup = R.getprogcoverage(budget=budget_outreachscaleup,
                                 t=2013,
                                 parset=P.parsets['default'],
                                 proportion=True)
    coverage_outreachscaleup_number = R.getprogcoverage(budget=budget_outreachscaleup,
                                 t=2013,
                                 parset=P.parsets['default'],
                                 proportion=False)
    
    R.covout['hivtest']['F 15-49'].interaction = 'nested'
    outcomes_nested_outreachscaleup = R.getoutcomes(coverage_outreachscaleup_number,
                                    t=2013,
                                    parset=P.parsets['default'])
    
    R.covout['hivtest']['F 15-49'].interaction = 'random'
    outcomes_random_outreachscaleup = R.getoutcomes(coverage_outreachscaleup_number,
                                    t=2013,
                                    parset=P.parsets['default'])
    
    R.covout['hivtest']['F 15-49'].interaction = 'additive'
    outcomes_additive_outreachscaleup = R.getoutcomes(coverage_outreachscaleup_number,
                                    t=2013,
                                    parset=P.parsets['default'])
    
    
    budget_hometestscaleup = {'HTC_clinics': array([ 1e7,]),
              'HTC_outreach': array([ 1e6,]),
              'HTC_hometest': array([ 1e7,])}
    
    coverage_hometestscaleup = R.getprogcoverage(budget=budget_hometestscaleup,
                                 t=2013,
                                 parset=P.parsets['default'],
                                 proportion=True)
    coverage_hometestscaleup_number = R.getprogcoverage(budget=budget_hometestscaleup,
                                 t=2013,
                                 parset=P.parsets['default'],
                                 proportion=False)
    
    R.covout['hivtest']['F 15-49'].interaction = 'nested'
    outcomes_nested_hometestscaleup = R.getoutcomes(coverage_hometestscaleup_number,
                                    t=2013,
                                    parset=P.parsets['default'])
    R.covout['hivtest']['F 15-49'].interaction = 'random'
    outcomes_random_hometestscaleup = R.getoutcomes(coverage_hometestscaleup_number,
                                    t=2013,
                                    parset=P.parsets['default'])
    R.covout['hivtest']['F 15-49'].interaction = 'additive'
    outcomes_additive_hometestscaleup = R.getoutcomes(coverage_hometestscaleup_number,
                                    t=2013,
                                    parset=P.parsets['default'])

    # Run tests
    assert_allclose(coverage['HTC_clinics'][0],testval_HTC_clinics_cov,atol=atol)
    assert_allclose(coverage['HTC_outreach'][0],testval_HTC_outreach_cov,atol=atol)
    assert_allclose(coverage['HTC_hometest'][0],testval_HTC_hometest_cov,atol=atol)
    
    assert_allclose(outcomes_nested['hivtest']['F 15-49'][0],testval_nested,atol=atol)
    assert_allclose(outcomes_random['hivtest']['F 15-49'][0],testval_random,atol=atol)
    assert_allclose(outcomes_additive['hivtest']['F 15-49'][0],testval_additive,atol=atol)
    
    assert_allclose(coverage_outreachscaleup['HTC_clinics'][0],0.244944433098,atol=atol)
    assert_allclose(coverage_outreachscaleup['HTC_outreach'][0], 0.217677365273,atol=atol)
    assert_allclose(coverage_outreachscaleup['HTC_hometest'][0], 0.0566322089804,atol=atol)
    
    assert_allclose(outcomes_nested_outreachscaleup['hivtest']['F 15-49'][0],0.444239953077,atol=atol)
    assert_allclose(outcomes_random_outreachscaleup['hivtest']['F 15-49'][0],0.52833307343,atol=atol)
    assert_allclose(outcomes_additive_outreachscaleup['hivtest']['F 15-49'][0],0.558741856611,atol=atol)
    
    assert_allclose(coverage_hometestscaleup['HTC_clinics'][0],0.244944433098,atol=atol) 
    assert_allclose(coverage_hometestscaleup['HTC_outreach'][0], 0.0227951129721,atol=atol)  
    assert_allclose(coverage_hometestscaleup['HTC_hometest'][0], 0.356286414635,atol=atol) 
    
    assert_allclose(outcomes_nested_hometestscaleup['hivtest']['F 15-49'][0],0.435885926,atol=atol)
    assert_allclose(outcomes_random_hometestscaleup['hivtest']['F 15-49'][0],0.461657257438,atol=atol)
    assert_allclose(outcomes_additive_hometestscaleup['hivtest']['F 15-49'][0],0.471777925796,atol=atol)
    

    # Now see how the different options affect diagnoses
    initialparsdict = R.getpars(coverage, t=2013, parset=P.parsets['default'])
    outreachparsdict = R.getpars(coverage_outreachscaleup_number, t=2013, parset=P.parsets['default'])
    hometestparsdict = R.getpars(coverage_hometestscaleup_number, t=2013, parset=P.parsets['default'])
    
    initialparset = dcp(P.parsets['default'])
    initialparset.pars = initialparsdict
    outreachparset = dcp(P.parsets['default'])
    outreachparset.pars = outreachparsdict
    hometestparset = dcp(P.parsets['default'])
    hometestparset.pars = hometestparsdict
    
    P.addparset(name='initial',parset=initialparset)
    P.addparset(name='outreach',parset=outreachparset)
    P.addparset(name='hometest',parset=hometestparset)
    
    epiresults_initial = P.runsim(name='initial')
    epiresults_outreach = P.runsim(name='outreach')
    epiresults_hometest = P.runsim(name='hometest')
    
    e1 = epiresults_initial.main['numdiag'].pops[0,1,16:].sum(axis=0)
    e2 = epiresults_outreach.main['numdiag'].pops[0,1,16:].sum(axis=0)
    e3 = epiresults_hometest.main['numdiag'].pops[0,1,16:].sum(axis=0)
    
    
    def summary_scaleup():
        ''' Print out useful information'''
        output = '\n'
        output += '===================================\n'
        output += 'Initial budget allocation:\n'
        output += ' Clinics: %s\n'    % budget['HTC_clinics'][0]
        output += ' Outreach: %s\n'    % budget['HTC_outreach'][0]
        output += ' Hometest: %s\n'    % budget['HTC_hometest'][0]
        output += 'Initial coverage:\n'
        output += ' Clinics: %s\n'    % coverage['HTC_clinics'][0]
        output += ' Outreach: %s\n'    % coverage['HTC_outreach'][0]
        output += ' Hometest: %s\n'    % coverage['HTC_hometest'][0]
        output += 'Initial outcomes:\n'
        output += '   Nested: %s\n'    % outcomes_nested['hivtest']['F 15-49'][0]
        output += '   Random: %s\n'    % outcomes_random['hivtest']['F 15-49'][0]
        output += ' Additive: %s\n'    % outcomes_additive['hivtest']['F 15-49'][0]
        output += '===================================\n'
        output += 'Budget with outreach scale-up:\n'
        output += ' Clinics: %s\n'    % budget_outreachscaleup['HTC_clinics'][0]
        output += ' Outreach: %s\n'    % budget_outreachscaleup['HTC_outreach'][0]
        output += ' Hometest: %s\n'    % budget_outreachscaleup['HTC_hometest'][0]
        output += 'Coverage with outreach scale-up:\n'
        output += ' Clinics: %s\n'    % coverage_outreachscaleup['HTC_clinics'][0]
        output += ' Outreach: %s\n'    % coverage_outreachscaleup['HTC_outreach'][0]
        output += ' Hometest: %s\n'    % coverage_outreachscaleup['HTC_hometest'][0]
        output += 'Outcomes with outreach scale-up:\n'
        output += '   Nested: %s\n'    % outcomes_nested_outreachscaleup['hivtest']['F 15-49'][0]
        output += '   Random: %s\n'    % outcomes_random_outreachscaleup['hivtest']['F 15-49'][0]
        output += ' Additive: %s\n'    % outcomes_additive_outreachscaleup['hivtest']['F 15-49'][0]
        output += '===================================\n'
        output += 'Budget with hometest scale-up:\n'
        output += ' Clinics: %s\n'    % budget_hometestscaleup['HTC_clinics'][0]
        output += ' Outreach: %s\n'    % budget_hometestscaleup['HTC_outreach'][0]
        output += ' Hometest: %s\n'    % budget_hometestscaleup['HTC_hometest'][0]
        output += 'Coverage with hometest scale-up:\n'
        output += ' Clinics: %s\n'    % coverage_hometestscaleup['HTC_clinics'][0]
        output += ' Outreach: %s\n'    % coverage_hometestscaleup['HTC_outreach'][0]
        output += ' Hometest: %s\n'    % coverage_hometestscaleup['HTC_hometest'][0]
        output += 'Outcomes with hometest scale-up:\n'
        output += '   Nested: %s\n' % outcomes_nested_hometestscaleup['hivtest']['F 15-49'][0]
        output += '   Random: %s\n' % outcomes_random_hometestscaleup['hivtest']['F 15-49'][0]
        output += ' Additive: %s\n' % outcomes_additive_hometestscaleup['hivtest']['F 15-49'][0]
        output += '===================================\n'
        output += '\n'
        output += '===================================\n'
        output += 'Diagnoses in Females 15-49 2016-2030:\n'
        output += '             Initial: %s\n'    % e1
        output += '   Outreach scale-up: %s\n'    % e2
        output += '  Home-test scale-up: %s\n'    % e3
        output += '===================================\n'
        print output
    
    if showstats: summary_scaleup()


if 'costcov' in tests:
    P = demo(doplot=False, which='simple')
    
    pops = P.pars()['popkeys']
    
    for saturation in [0.01, 0.99]:
        for unitcost in [1., 10.]:
            print('\n\n\nCurrent saturation: %s' % saturation)
            print('Current unit cost: %s\n' % unitcost)
        
            sat1 = saturation
            sat2 = saturation
            uc1 = unitcost
            uc2 = unitcost
            cost = 1e6
            cov = 1e6
            
            HTC_1 = Program(short='HTC_1',
                               name='Testing program 1',
                               targetpars=[{'param': 'hivtest', 'pop': pop} for pop in pops],
                               targetpops=pops,
                               category='Testing')
            HTC_1.costcovfn.addccopar({'saturation': sat1, 't': 2016.0, 'unitcost': uc1})
            HTC_1.addcostcovdatum({'t':2016, 'cost':cost, 'coverage':cov})
            
            HTC_2 = Program(short='HTC_2',
                               name='Testing program 2',
                               targetpars=[{'param': 'hivtest', 'pop': pop} for pop in pops],
                               targetpops=pops,
                               category='Testing')
            HTC_2.costcovfn.addccopar({'saturation': sat1, 't': 2016.0, 'unitcost': uc2})
            HTC_2.addcostcovdatum({'t':2016, 'cost':cost, 'coverage':cov})
            
            P.progset().addprograms([HTC_1, HTC_2])
            
            for pop in pops:
                P.progset().covout['hivtest'][pop].ccopars = odict({'intercept': [0.0], 'HTC':[1.0], 'HTC_1':[1.0], 'HTC_2':[1.0], 't': [2016]})
            
            print('Comparison:')
            comparison = P.progset().compareoutcomes(parset=P.parset(), year=2016, doprint=True)
            coverage = P.progset().getdefaultcoverage(t=2016, parset=P.parset())
            print('\nCoverage:')
            print(coverage)
            #P.runsim()
            #op.pygui(P)