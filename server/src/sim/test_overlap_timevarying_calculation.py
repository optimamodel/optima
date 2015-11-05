import sys
sys.path.append('..')
import optima
from liboptima.utils import dict_equal
from copy import deepcopy
import unittest
import numpy
from pylab import *
from numpy import arange,linspace
import optima.ccocs as ccocs

ps = optima.ProgramSet('Test')
cc_inputs = [dict()]
cc_inputs[0]['pop'] = 'testpop'
cc_inputs[0]['form'] = 'co_cofun'
cc_inputs[0]['fe_params'] = [0, 0, 1, 1] # Linear coverage
co_inputs = [dict()]
co_inputs[0]['pop'] = 'testpop'
co_inputs[0]['param'] = 'testpar'
co_inputs[0]['form'] = 'co_cofun'
co_inputs[0]['fe_params'] = [0.1,0.1, 0.6, 0.6] 
ps.programs.append(optima.Program('P1',deepcopy(cc_inputs),deepcopy(co_inputs)))
co_inputs[0]['fe_params'] = [0.1,0.1, 0.7, 0.7] 
ps.programs.append(optima.Program('P2',deepcopy(cc_inputs),deepcopy(co_inputs)))
co_inputs[0]['fe_params'] = [0.1,0.1, 0.2, 0.2] 
ps.programs.append(optima.Program('P3',deepcopy(cc_inputs),deepcopy(co_inputs)))

# Check that the program works
p = ps.programs[1] # Pick the second program, for 2x coverage

# Make the triple program budget
tvec = numpy.array([2015,2020,2025,2030])
budget = numpy.array(([0.1,0.2,0.5,1],[0.2,0.2,0.2,0.2],[0.3,0.3,0.3,0.3]))
# Test against the spreadsheet with various program 1 coverage levels

# These are at a snapshot of with program 2 at 0.7 and program 3 and 0.2
print '2015'
ps.specific_reachability_interaction['testpop']['testpar'] = 'additive'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']
ps.specific_reachability_interaction['testpop']['testpar'] = 'nested'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']
ps.specific_reachability_interaction['testpop']['testpar'] = 'random'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']

ps['P2'].coverage_outcome['testpop']['testpar'].fe_params = [0.1,0.1, 0.6, 0.6] 
ps['P3'].coverage_outcome['testpop']['testpar'].fe_params = [0.1,0.1, 0.3, 0.3] 
print '2020'
ps.specific_reachability_interaction['testpop']['testpar'] = 'additive'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']
ps.specific_reachability_interaction['testpop']['testpar'] = 'nested'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']
ps.specific_reachability_interaction['testpop']['testpar'] = 'random'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']

# Let's say that from 2015 to 2030 the parameter changes by 0.3. So we get 0.1 difference at each time.
# Then we will have in 2030

ps['P2'].coverage_outcome['testpop']['testpar'].fe_params = [0.1,0.1, 0.5, 0.5] 
ps['P3'].coverage_outcome['testpop']['testpar'].fe_params = [0.1,0.1, 0.4, 0.4] 
print '2025'
ps.specific_reachability_interaction['testpop']['testpar'] = 'additive'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']
ps.specific_reachability_interaction['testpop']['testpar'] = 'nested'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']
ps.specific_reachability_interaction['testpop']['testpar'] = 'random'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']

ps['P2'].coverage_outcome['testpop']['testpar'].fe_params = [0.1,0.1, 0.4, 0.4] 
ps['P3'].coverage_outcome['testpop']['testpar'].fe_params = [0.1,0.1, 0.5, 0.5] 
print '2030'
ps.specific_reachability_interaction['testpop']['testpar'] = 'additive'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']
ps.specific_reachability_interaction['testpop']['testpar'] = 'nested'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']
ps.specific_reachability_interaction['testpop']['testpar'] = 'random'
print ps.get_outcomes(tvec,budget)['testpop']['testpar']

