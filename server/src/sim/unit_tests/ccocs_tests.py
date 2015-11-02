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

class TestCCOCs(unittest.TestCase):

	def test_scaleup(self):
		# Make a normal type program and test expected output
		ccdata = {u'coveragelower': 0.1, u'nonhivdalys': 1.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.9, u'scaleup': 0.73}
		cost_coverage = ccocs.cc_scaleup(ccdata)

		codata = [0, 0, 0.5, 0.5] # Linear coverage-outcome from 0 to 1 exactly
		coverage_outcome = ccocs.co_cofun(codata)

		# Various tests here
		c = cost_coverage.evaluate(300000.0)
		c2 = cost_coverage.evaluate(100000000.0)
		outcomes = coverage_outcome.evaluate(c)

		self.assertAlmostEqual(c2,numpy.array([0.98]),places=7) 
		self.assertAlmostEqual(c,numpy.array([0.5]),places=7) 
		self.assertAlmostEqual(c,2*outcomes,places=7) 

	def test_linear(self):
		# Test linear CC and CO functions (for testing modalities)
		codata = [2.0, 0.0]
		coverage_outcome = ccocs.co_linear(codata)

		self.assertAlmostEqual(coverage_outcome.evaluate(0.0),0,places=7) 
		self.assertAlmostEqual(coverage_outcome.evaluate(0.5),1,places=7) 
		self.assertAlmostEqual(coverage_outcome.evaluate(1.0),2,places=7) 

	def test_co_cofun(self):

		codata = [0, 0, 2, 2] # Linear coverage-outcome from 0 to 1 exactly
		coverage_outcome = ccocs.co_cofun(codata)

		self.assertAlmostEqual(coverage_outcome.evaluate(0.0),0,places=7) 
		self.assertAlmostEqual(coverage_outcome.evaluate(0.5),1,places=7) 
		self.assertAlmostEqual(coverage_outcome.evaluate(1.0),2,places=7) 

		self.assertAlmostEqual(coverage_outcome.invert(0.0),0,places=7) 
		self.assertAlmostEqual(coverage_outcome.invert(1.0),0.5,places=7) 
		self.assertAlmostEqual(coverage_outcome.invert(2.0),1.0,places=7) 


	def test_tofromdict(self):
		codata = [0, 0, 2, 2] # Linear coverage-outcome from 0 to 1 exactly
		co = ccocs.co_cofun(codata)
		cdict = co.todict()
		co2 = ccocs.ccoc.fromdict(cdict)
		self.assertEqual(co.evaluate(0.0),co2.evaluate(0.0)) 
		self.assertEqual(co.evaluate(1.0),co2.evaluate(1.0)) 
		self.assertEqual(co.evaluate(2.0),co2.evaluate(2.0)) 

	def test_overlap_1(self):
		# Make a programset for testing
		ps = optima.ProgramSet('Test')
		cc_inputs = [dict()]
		cc_inputs[0]['pop'] = 'testpop'
		cc_inputs[0]['form'] = 'co_cofun'
		cc_inputs[0]['fe_params'] = [0, 0, 1, 1] # Linear coverage
		co_inputs = [dict()]
		co_inputs[0]['pop'] = 'testpop'
		co_inputs[0]['param'] = 'testpar'
		co_inputs[0]['form'] = 'co_cofun'
		co_inputs[0]['fe_params'] = [0, 0, 1, 1] # Outcome is 1x coverage
		ps.programs.append(optima.Program('P1',deepcopy(cc_inputs),deepcopy(co_inputs)))
		co_inputs[0]['fe_params'] = [0, 0, 2, 2] # Outcome is 2x coverage
		ps.programs.append(optima.Program('P2',deepcopy(cc_inputs),deepcopy(co_inputs)))
		co_inputs[0]['fe_params'] = [0, 0, 3, 3] # Outcome is 3x coverage
		ps.programs.append(optima.Program('P3',deepcopy(cc_inputs),deepcopy(co_inputs)))
		co_inputs[0]['param'] = 'testpar2' # This program is just along for the ride. It's presence is not *supposed* to affect the calculation
		ps.programs.append(optima.Program('P4',deepcopy(cc_inputs),deepcopy(co_inputs)))

		# Check that the program works
		p = ps.programs[1] # Pick the second program, for 2x coverage

		# Program coverage should match 'spending' here
		self.assertEqual(p.get_coverage('testpop',0),0) 
		self.assertEqual(p.get_coverage('testpop',0.3),0.3) 
		self.assertEqual(p.get_coverage('testpop',1),1) 

		# Program effect should be twice the coverage
		self.assertEqual(p.get_outcome('testpop','testpar',0),0) 
		self.assertEqual(p.get_outcome('testpop','testpar',0.3),0.6) 
		self.assertEqual(p.get_outcome('testpop','testpar',1),2) 

		# Make the triple program budget
		tvec_1d = numpy.array([1])
		tvec_2d = numpy.array([1,2])
		budget_1d = numpy.array(([0.2,0.3,0.4,0.4])) # Here is the spending
		budget_1d.shape = (4,1)
		# Note that a 2d budget has time in rows
		budget_2d = numpy.array(([0.2,0.2],[0.3,0.3],[0.4,0.4],[0.4,0.4])) # Here is the spending
		budget_2d.shape = (4,2)
		# Note - the effects should be
		# COVERAGE: 0.2,0.3,0.4
		# OUTCOME: 0.2,0.6,1.2
		# at both times in the 2d case

		# Test additive
		ps.specific_reachability_interaction['testpop']['testpar'] = 'additive'
		numpy.testing.assert_allclose(ps.get_outcomes(tvec_1d,budget_1d)['testpop']['testpar'],[2.0])
		numpy.testing.assert_allclose(ps.get_outcomes(tvec_2d,budget_2d)['testpop']['testpar'],[2.0,2.0])

		# Test nested
		# COVERAGE: 0.2,0.3,0.4
		# DELTA_OUT = 3
		# OUTCOME: 0.2,0.6,1.2
		# For Outcome =c3*max(delta_out1,delta_out2,delta_out3) + (c2-c3)*max(delta_out1,delta_out2) + (c1 -c2)*delta_out1, where c3<c2<c1.
		# we should have
		# 0.2*3 + 0.1*3 + 0.1*3 = 0.4*3 = 1.2
		ps.specific_reachability_interaction['testpop']['testpar'] = 'nested'
		numpy.testing.assert_allclose(ps.get_outcomes(tvec_1d,budget_1d)['testpop']['testpar'],[1.2])
		numpy.testing.assert_allclose(ps.get_outcomes(tvec_2d,budget_2d)['testpop']['testpar'],[1.2,1.2])

if __name__ == '__main__':
	# Run all tests
    # unittest.main()

    # Only run particular tests
    suite = unittest.TestSuite()
    suite.addTest(TestCCOCs('test_overlap_1'))
    unittest.TextTestRunner().run(suite)

