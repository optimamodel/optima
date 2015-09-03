import sys
sys.path.append('..')
import optima
from liboptima.utils import dict_equal
from copy import deepcopy
import unittest
import numpy
from pylab import *
from numpy import arange,linspace

class TestCCOCs(unittest.TestCase):

	def test_scaleup(self):
		# Make a normal type program and test expected output
		ccdata = {u'coveragelower': 0.1, u'nonhivdalys': 1.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.9, u'scaleup': 0.73}
		cost_coverage = optima.ccocs.cc_scaleup(ccdata)

		codata = [0, 0, 0.5, 0.5] # Linear coverage-outcome from 0 to 1 exactly
		coverage_outcome = optima.ccocs.co_cofun(codata)

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
		coverage_outcome = optima.ccocs.co_linear(codata)

		self.assertAlmostEqual(coverage_outcome.evaluate(0.0),0,places=7) 
		self.assertAlmostEqual(coverage_outcome.evaluate(0.5),1,places=7) 
		self.assertAlmostEqual(coverage_outcome.evaluate(1.0),2,places=7) 

	def test_co_cofun(self):

		codata = [0, 0, 2, 2] # Linear coverage-outcome from 0 to 1 exactly
		coverage_outcome = optima.ccocs.co_cofun(codata)

		self.assertAlmostEqual(coverage_outcome.evaluate(0.0),0,places=7) 
		self.assertAlmostEqual(coverage_outcome.evaluate(0.5),1,places=7) 
		self.assertAlmostEqual(coverage_outcome.evaluate(1.0),2,places=7) 

		self.assertAlmostEqual(coverage_outcome.invert(0.0),0,places=7) 
		self.assertAlmostEqual(coverage_outcome.invert(1.0),0.5,places=7) 
		self.assertAlmostEqual(coverage_outcome.invert(2.0),1.0,places=7) 

if __name__ == '__main__':
    unittest.main()


