"""
Test script for service modalities

Details:
Three different programs are targeting testing rates for Females 15-49.
This script demonstrates the effect of these programs under different interaction assumptions.
It can also be used as a test script, to ensure that the calculations are being done correctly.

Version: 2015dec01 by robyns
"""


print('Testing service modalities...')
from optima import Project, Program, Programset
from numpy import array
from numpy.testing import assert_allclose
# Uncomment the line below to disable the assert statements and run through to completion
#assert_allclose = lambda x,y: True

P = Project(spreadsheet='test.xlsx')

doplot = False
eps = 1e-3
testval_nested = 0.42475173
testval_random = 0.43792895
testval_additive = 0.44181250

# First set up some programs
HTC_clinics = Program(name='HTC_clinics',
              targetpars=[{'param': 'hivtest', 'pop': 'Females 15-49'}],
              targetpops=['Females 15-49'])

HTC_outreach = Program(name='HTC_outreach',
              targetpars=[{'param': 'hivtest', 'pop': 'Females 15-49'}],
              targetpops=['Females 15-49'])
               
HTC_hometest = Program(name='HTC_hometest',
              targetpars=[{'param': 'hivtest', 'pop': 'Females 15-49'}],
              targetpops=['Females 15-49'])

# Add cost-coverage function parameters to each program
HTC_clinics.costcovfn.addccopar({'t': 2013.0,
                                 'saturation':0.4,
                                 'unitcost': 40})
                         
HTC_outreach.costcovfn.addccopar({'t': 2013.0,
                                 'saturation':0.6,
                                  'unitcost': 50})
                         
HTC_hometest.costcovfn.addccopar({'t': 2013.0,
                                 'saturation':0.4,
                                  'unitcost': 10})

# Combine the 3 program together in a program set
R = Programset(programs=[HTC_clinics,HTC_outreach,HTC_hometest])

# Add parameters for the coverage-outcome functions
R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.3,
                                                't': 2013.0,
                                                'HTC_clinics': 0.5,
                                                'HTC_outreach': 0.6,
                                                'HTC_hometest':0.1})
                    
# Define the budget and the type of interaction
budget = {'HTC_clinics': array([ 1e7,]),
          'HTC_outreach': array([ 1e6,]),
          'HTC_hometest': array([ 1e6,])}

# Plot the cost-coverage curves for each program if asked
if doplot: R.plotallcoverage(t=[2013],
                  parset=P.parsets['default'],
                  xupperlim=1e8)

# Get the coverage of each program associated with this budget
coverage = R.getprogcoverage(budget=budget,
                             t=[2013],
                             parset=P.parsets['default'],
                             proportion=True)


# Get the outcomes associated with this budget
outcomes_nested = R.getoutcomes(coverage,
                                t=[2013],
                                parset=P.parsets['default'])

outcomes_random = R.getoutcomes(coverage,
                                t=[2013],
                                parset=P.parsets['default'])

outcomes_additive = R.getoutcomes(coverage,
                                t=[2013],
                                parset=P.parsets['default'])

assert_allclose(outcomes_nested['hivtest']['Females 15-49'][0],testval_nested)
assert_allclose(outcomes_random['hivtest']['Females 15-49'][0],testval_random)
assert_allclose(outcomes_additive['hivtest']['Females 15-49'][0],testval_additive)

output = '\n'
output += '===================================\n'
output += 'Calculated outcomes\n'
output += '   Nested: %s\n'    % outcomes_nested['hivtest']['Females 15-49'][0]
output += '   Random: %s\n'    % outcomes_random['hivtest']['Females 15-49'][0]
output += ' Additive: %s\n'    % outcomes_additive['hivtest']['Females 15-49'][0]
output += '===================================\n'
output += 'Outcomes should be:\n'
output += '   Nested: %s\n'    % testval_nested
output += '   Random: %s\n'    % testval_random
output += ' Additive: %s\n'    % testval_additive
output += '===================================\n'
print output


# See the effect of scaling up one of the programs
budget_outreachscaleup = {'HTC_clinics': array([ 1e7,]),
          'HTC_outreach': array([ 1e7,]),
          'HTC_hometest': array([ 1e6,])}

coverage_outreachscaleup = R.getprogcoverage(budget=budget_outreachscaleup,
                             t=[2013],
                             parset=P.parsets['default'],
                             proportion=True)

outcomes_nested_outreachscaleup = R.getoutcomes(coverage_outreachscaleup,
                                t=[2013],
                                parset=P.parsets['default'])

outcomes_random_outreachscaleup = R.getoutcomes(coverage_outreachscaleup,
                                t=[2013],
                                parset=P.parsets['default'])

outcomes_additive_outreachscaleup = R.getoutcomes(coverage_outreachscaleup,
                                t=[2013],
                                parset=P.parsets['default'])


budget_hometestscaleup = {'HTC_clinics': array([ 1e7,]),
          'HTC_outreach': array([ 1e6,]),
          'HTC_hometest': array([ 1e7,])}

coverage_hometestscaleup = R.getprogcoverage(budget=budget_hometestscaleup,
                             t=[2013],
                             parset=P.parsets['default'],
                             proportion=True)

outcomes_nested_hometestscaleup = R.getoutcomes(coverage_hometestscaleup,
                                t=[2013],
                                parset=P.parsets['default'])

outcomes_random_hometestscaleup = R.getoutcomes(coverage_hometestscaleup,
                                t=[2013],
                                parset=P.parsets['default'])

outcomes_additive_hometestscaleup = R.getoutcomes(coverage_hometestscaleup,
                                t=[2013],
                                parset=P.parsets['default'])

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

assert_allclose(coverage['HTC_clinics'][0],0.244944433098)
assert_allclose(coverage['HTC_outreach'][0],0.0227951129721)
assert_allclose(coverage['HTC_hometest'][0],0.0566322089804)

output += 'Initial outcomes:\n'
output += '   Nested: %s\n'    % outcomes_nested['hivtest']['Females 15-49'][0]
output += '   Random: %s\n'    % outcomes_random['hivtest']['Females 15-49'][0]
output += ' Additive: %s\n'    % outcomes_additive['hivtest']['Females 15-49'][0]

assert_allclose(outcomes_nested['hivtest']['Females 15-49'][0],0.424751727846)
assert_allclose(outcomes_random['hivtest']['Females 15-49'][0],0.437386196025)
assert_allclose(outcomes_additive['hivtest']['Females 15-49'][0],0.441812505231)

output += '===================================\n'
output += 'Budget with outreach scale-up:\n'

output += ' Clinics: %s\n'    % budget_outreachscaleup['HTC_clinics'][0]
output += ' Outreach: %s\n'    % budget_outreachscaleup['HTC_outreach'][0]
output += ' Hometest: %s\n'    % budget_outreachscaleup['HTC_hometest'][0]

output += 'Coverage with outreach scale-up:\n'
output += ' Clinics: %s\n'     % coverage_outreachscaleup['HTC_clinics'][0]
output += ' Outreach: %s\n'    % coverage_outreachscaleup['HTC_outreach'][0]
output += ' Hometest: %s\n'    % coverage_outreachscaleup['HTC_hometest'][0]
assert_allclose(coverage_outreachscaleup['HTC_clinics'][0],0.244944433098)
assert_allclose(coverage_outreachscaleup['HTC_outreach'][0], 0.217677365273)
assert_allclose(coverage_outreachscaleup['HTC_hometest'][0], 0.0566322089804)

output += 'Outcomes with outreach scale-up:\n'
output += '   Nested: %s\n'    % outcomes_nested_outreachscaleup['hivtest']['Females 15-49'][0]
output += '   Random: %s\n'    % outcomes_random_outreachscaleup['hivtest']['Females 15-49'][0]
output += ' Additive: %s\n'    % outcomes_additive_outreachscaleup['hivtest']['Females 15-49'][0]
assert_allclose(outcomes_nested_outreachscaleup['hivtest']['Females 15-49'][0],0.444239953077)
assert_allclose(outcomes_random_outreachscaleup['hivtest']['Females 15-49'][0],0.52833307343)
assert_allclose(outcomes_additive_outreachscaleup['hivtest']['Females 15-49'][0],0.558741856611)


output += '===================================\n'
output += 'Budget with hometest scale-up:\n'

output += ' Clinics: %s\n'     % budget_hometestscaleup['HTC_clinics'][0]
output += ' Outreach: %s\n'    % budget_hometestscaleup['HTC_outreach'][0]
output += ' Hometest: %s\n'    % budget_hometestscaleup['HTC_hometest'][0]

output += 'Coverage with hometest scale-up:\n'
output += ' Clinics: %s\n'     % coverage_hometestscaleup['HTC_clinics'][0]
output += ' Outreach: %s\n'    % coverage_hometestscaleup['HTC_outreach'][0]
output += ' Hometest: %s\n'    % coverage_hometestscaleup['HTC_hometest'][0]
assert_allclose(coverage_hometestscaleup['HTC_clinics'][0],0.244944433098) 
assert_allclose(coverage_hometestscaleup['HTC_outreach'][0], 0.0227951129721)  
assert_allclose(coverage_hometestscaleup['HTC_hometest'][0], 0.356286414635) 

output += 'Outcomes with hometest scale-up:\n'
output += '   Nested: %s\n' % outcomes_nested_hometestscaleup['hivtest']['Females 15-49'][0]
output += '   Random: %s\n' % outcomes_random_hometestscaleup['hivtest']['Females 15-49'][0]
output += ' Additive: %s\n' % outcomes_additive_hometestscaleup['hivtest']['Females 15-49'][0]
assert_allclose(outcomes_nested_hometestscaleup['hivtest']['Females 15-49'][0],0.435885926)
assert_allclose(outcomes_random_hometestscaleup['hivtest']['Females 15-49'][0],0.461657257438)
assert_allclose(outcomes_additive_hometestscaleup['hivtest']['Females 15-49'][0],0.471777925796)

output += '===================================\n'
print output

initialparset = R.getparset(coverage,t=[2013], parset=P.parsets['default'])
outreachparset = R.getparset(coverage_outreachscaleup,t=[2013], parset=P.parsets['default'])
hometestparset = R.getparset(coverage_hometestscaleup,t=[2013], parset=P.parsets['default'])

P.addparset(name='initial',parset=initialparset)
P.addparset(name='outreach',parset=outreachparset)
P.addparset(name='hometest',parset=hometestparset)

epiresults_initial = P.runsim(name='initial')
epiresults_outreach = P.runsim(name='outreach')
epiresults_hometest = P.runsim(name='hometest')

e1 = epiresults_initial.main['numdiag'].pops[0,1,75:].sum(axis=0)
e2 = epiresults_outreach.main['numdiag'].pops[0,1,75:].sum(axis=0)
e3 = epiresults_hometest.main['numdiag'].pops[0,1,75:].sum(axis=0)

# TODO: Some checks on the values of e1-e3 here

output = '\n'
output += '===================================\n'
output += 'Diagnoses in Females 15-40 2015-2030:\n'
output += '             Initial: %s\n'    % e1
output += '   Outreach scale-up: %s\n'    % e2
output += '  Home-test scale-up: %s\n'    % e3
output += '===================================\n'
print output

