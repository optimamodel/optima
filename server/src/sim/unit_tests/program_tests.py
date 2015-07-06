import sys
sys.path.append('../tests')
import add_optima_paths
from extra_utils import dict_equal
from copy import deepcopy
import unittest
import numpy
import region
import program
from pylab import *
from numpy import arange,linspace

default_effects = {'paramtype':'normal','popname':'FSW','param':['testing'],'iscoverageparam':False}
p = program.Program('FSW','FSW programs',default_effects)
ccdata = {'function': 'cceqn', 'parameters': {u'coveragelower': 0.2, u'nonhivdalys': 0.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.75, u'scaleup': 0.73}}
codata = [{'function': 'coeqn', 'parameters': [0.2, 0.25, 0.8, 0.85]}, {'function': 'coeqn', 'parameters': [0.7949999999999999, 0.835, 0.96, 1]}, {'function': 'coeqn', 'parameters': [0.78, 0.8200000000000001, 0.96, 1]}]
m = p.add_modality('M1',ccdata,codata)

class TestPrograms(unittest.TestCase):

	def test_normal(self):
		# Make a normal type program and test expected output
		p = program.Program('short_name','full_name',default_effects)
		ccdata = {'function': 'cceqn', 'parameters': {u'coveragelower': 0.1, u'nonhivdalys': 1.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.9, u'scaleup': 0.73}}
		codata = [{'function': 'coeqn', 'parameters': [0, 0, 0.5, 0.5]}] # Linear coverage-outcome from 0 to 1 exactly
		m = p.add_modality('modality_name',ccdata,codata)

		# Various tests here
		c = p.get_coverage(300000.0)
		c2 = p.get_coverage(100000000.0)
		outcomes = p.get_outcomes(c)

		self.assertAlmostEqual(c2[0],numpy.array([0.98]),places=7) # Max coverage is saturation
		self.assertAlmostEqual(c[0],numpy.array([0.5]),places=7) # Max coverage is saturation
		self.assertAlmostEqual(c[0],2*outcomes[0],places=7) # Max coverage is saturation


	def test_coverage(self): 
		# Test coverage type programs
		return

	def test_spending(self):
		# Test spending only programs
		return

	def test_modalities(self):
		# Test overlapping modalities
		return



	def test_plot(self):
		# Make a plot of the CC, CO and CCO curves (the same as the web interface)
		return True # Temporarily disable this test
		p1 = deepcopy(p)
		
		spending = linspace(0.0,5e6,100)

		# Plot cost-coverage
		coverage = m.get_coverage(spending)
		figure(1)
		plot(spending, coverage)

		# Plot coverage-outcome
		outcomes = m.get_outcomes(coverage)
		f, axarr = subplots(len(outcomes), sharex=True)
		count = 0
		for outcome in outcomes:
			axarr[count].plot(coverage,outcome)
			axarr[count].set_ylim([0,1])
			count += 1

		# Plot cost-coverage-outcome
		f, axarr = subplots(len(outcomes), sharex=True)
		count = 0
		for outcome in outcomes:
			axarr[count].plot(spending,outcome)
			axarr[count].set_ylim([0,1])
			count += 1
		show()
		print p
		print m




# Let's say modality 1 can reach 100% of the population, but modalities 2 and 3 can reach 50%. Then
# (1) - 1
# (2) - 0.5
# (3) - 0.5
# (1,2) = 1*0.5
# (1,3) = 1*0.5
# (2,3) = 0.5*0.5 = 0.25
# (1,2,3) = 1*0.5*0.5 = 0.25

# This includes double counting
# Now, we remove the double counting
# The unique coverage we want is
# (1) - 0.25
# (2) - 0
# (3) - 0
# (1,2) = 0.25
# (1,3) = 0.25
# (2,3) = 0
# (1,2,3) = 0.25

# Algorithmically, we go
# 0.25 people are in (1,2,3), so they get subtracted from any population containing them


# Then we have 50% of the population reached only by modality 1
# 



if __name__ == '__main__':
    unittest.main()


