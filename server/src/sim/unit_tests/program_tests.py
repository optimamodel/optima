import sys
sys.path.append('../tests')
import add_optima_paths
from extra_utils import dict_equal
from copy import deepcopy
import unittest
import numpy
import project
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
		p = program.Program('short_name','full_name',default_effects)
		ccdata = {'function': 'cceqn', 'parameters': {u'coveragelower': 0.1, u'nonhivdalys': 1.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.9, u'scaleup': 0.73}}
		codata = [{'function': 'identity', 'parameters': None}] # Linear coverage-outcome from 0 to 1 exactly
		m = p.add_modality('modality_name',ccdata,codata)

		# Various tests here
		c = p.get_coverage(300000.0)
		outcomes = p.get_outcomes(c)

		self.assertAlmostEqual(c[0],numpy.array([0.5]),places=7) # The expected coverage for this curve 
		self.assertEqual(c[0],outcomes[0]) # The outcome should be exactly the same as the coverage


	def test_spending(self):
		# Test spending only programs - should return 0 coverage and 0 outcome
		p = program.Program('short_name','full_name',default_effects)
		m = p.add_modality('null')

		# Various tests here
		c = p.get_coverage(300000.0)
		outcomes = p.get_outcomes(c)

		self.assertEqual(c[0],numpy.array([0])) # The expected coverage for this curve 
		self.assertEqual(outcomes[0],0) # The outcome should be exactly the same as the coverage

	def test_linear(self):
		# Test linear CC and CO functions (for testing modalities)
		p = program.Program('short_name','full_name',default_effects)
		ccdata = {'function': 'linear', 'parameters': [2.0, 0.0]}
		codata = [{'function': 'linear', 'parameters': [2.0, 0.0]}] 
		m1 = p.add_modality('modality_name',ccdata,codata)

		self.assertAlmostEqual(p.get_coverage(0.0)[0],0,places=7) 
		self.assertAlmostEqual(p.get_coverage(0.5)[0],1,places=7) 
		self.assertAlmostEqual(p.get_coverage(1.0)[0],2,places=7) 

		self.assertAlmostEqual(p.get_outcomes([0.0])[0],0,places=7) 
		self.assertAlmostEqual(p.get_outcomes([0.5])[0],1,places=7) 
		self.assertAlmostEqual(p.get_outcomes([1.0])[0],2,places=7) 

		return

	def test_modalities(self):
		# Test overlapping modalities

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



		return

	def test_overlapping_coverage(self):
		# Test overlapping coverage only
		print "ENTERING DEBUG"
		p = program.Program('short_name','full_name',default_effects)
		ccdata = {'function': 'linear', 'parameters': [1.0, 0.0]}
		codata = [{'function': 'identity', 'parameters': None}] # Linear coverage-outcome from 0 to 1 exactly
		m1 = p.add_modality('M1',ccdata,codata)
		m2 = p.add_modality('M2',ccdata,codata)

		def validate(m1,m2,mm1,mm2,mm3):
			# TESTS - if we have
			# m1, m2
			# mm1 = m1
			# mm2 = m2
			# mm3 = m1+m2
			# Then mm1 = mm3 == m1/2
			# m2 - mm3 = mm2

			self.assertAlmostEqual(mm1,mm3,places=7) 
			self.assertAlmostEqual(mm1,m1/2,places=7) 
			self.assertAlmostEqual(m2-mm3,mm2,places=7) 


		c = p.get_coverage(numpy.array([[0.5],[0.5]]))
		validate(0.5,0.5,c[0],c[2],c[1])

		c = p.get_coverage(numpy.array([[0.25],[0.5]]))
		validate(0.25,0.5,c[0],c[2],c[1])

		c = p.get_coverage(numpy.array([[0.0],[0.5]]))
		validate(0.0,0.5,c[0],c[2],c[1])

		c = p.get_coverage(numpy.array([[0.5],[0.0]]))
		validate(0.5,0.0,c[0],c[2],c[1])
		
		return
		
	def test_overlapping_spending(self):
		# Test overlapping spending only
		return
			
	def test_overlapping_coverage_noncoverage(self):
		# Test metamodalities with 2x normal modalities, and 2x coverage only modalities
		return


	def test_overlapping_mixture(self):
		# Test metamodalities with a mixture of normal, coverage, and spending only
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


