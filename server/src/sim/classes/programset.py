import uuid
from operator import mul
import defaults
from collections import defaultdict
import ccocs

coverage_params = ['numcircum','numost','numpmtct','numfirstline','numsecondline'] # This list is copied from makeccocs.py

class ProgramSet(object):
	# This class is a collection of programs/modalities
	def __init__(self,name):
		self.name = name
		self.uuid = str(uuid.uuid4())
		self.programs = []

		# self.modalities = []
		# self.metamodalities = [] # One metamodality for every combination of modalities, including single modalities
		# self.effective_coverage = [] # An effective coverage for every metamodality

		self.reachability_interaction = 'random' # These are the options on slide 7 of the proposal
		self.current_version = 1
		# The reachability interaction enables the metamodality maxcoverage to be automatically set

		# This stores the list of effects. Each modality and metamodality must contain a coverage-outcome
		# curve for each effect in the Program
		# May require effects as an argument to the constructor later?

	@classmethod
	def import_legacy(ProgramSet,name,programdata):
		# In legacy projects, the programdata list contains one entry per program
		ps = ProgramSet(name)
		ps.programs = [] # Make sure we start with an empty program list
		
		for prog in programdata:
			cc_inputs = []
			co_inputs = []

			if not prog['effects']: 
				# A program without any effects is a spending-only program
				cc_input = {}
				cc_input['pop'] = None
				cc_input['form'] = 'null'
				cc_input['fe_params'] = None
				cc_inputs.append(cc_input)
				
				co_input = {}
				co_input['pop'] = None
				co_input['param'] = None
				co_input['form'] = 'null'
				co_input['fe_params'] = None
				co_inputs.append(co_input)
			else:
				target_pops = list(set([effect['popname'] for effect in prog['effects']])) # Unique list of affected populations. In legacy programs, they all share the same CC curve
				
				for pop in target_pops:
					cc_input = {}
					cc_input['pop'] = pop
					if 'scaleup' in prog['ccparams'].keys():
						cc_input['form'] = 'cc_scaleup'
					else:
						cc_input['form'] = 'cc_noscaleup'
					cc_input['fe_params'] = prog['ccparams']
					cc_inputs.append(cc_input)

				for effect in prog['effects']:
					co_input = {}
					co_input['pop'] = effect['popname']
					co_input['param'] = effect['param']

					if effect['param'] in coverage_params: 
						co_input['form'] = 'identity'
						co_input['fe_params'] = None
					else:
						co_input['form'] = 'co_cofun'
						co_input['fe_params'] = effect['coparams']
					
					co_inputs.append(co_input)

			ps.programs.append(Program(prog['name'],cc_inputs,co_inputs,prog['nonhivdalys']))

		return ps


	def get_coverage(self,spending):
		# This function returns an array of effective coverage values for each metamodality
		# reflow_metamodalities should generally be run before this function is called
		# this is meant to happen automatically when add_modality() or remove_modality is called()
		#
		# Note that coverage is *supposed* to always be in normalized units (i.e. percentage of population)
		# The method program.convert_units() does the conversion to number of people at the last minute
		
		if len(self.modalities) == 1:
			spending = array([[spending]]) # Need a better solution...

		assert(len(spending)==len(self.modalities))

		# First, get the temporary coverage for each modality
		for i in xrange(0,len(spending)):
			self.modalities[i].temp_coverage = self.modalities[i].get_coverage(spending[i,:])
		
		print self.modalities[0].temp_coverage

		# Now compute the metamodality coverage
		if self.reachability_interaction == 'random':
			for mm in self.metamodalities:
				mm.temp_coverage1 = reduce(mul,[m.temp_coverage for m in self.modalities if m.uuid in mm.modalities]) # This is the total fraction reached
				
			for i in xrange(len(self.modalities),0,-1): # Iterate over metamodalities containing i modalities
				superset = [mm for mm in self.metamodalities if len(mm.modalities) >= i]
				subset = [mm for mm in self.metamodalities if len(mm.modalities) == i-1]

				for sub in subset:
					for sup in superset: 
						if set(sub.modalities).issubset(set(sup.modalities)):
							sub.temp_coverage1 -= sup.temp_coverage1

		print 'rerun'					
		print self.modalities[0].temp_coverage


		# Next, calculate the coverage for each metamodality
		effective_coverage = [mm.temp_coverage1 for mm in self.metamodalities]
		
		return effective_coverage

	def get_outcomes(self,effective_coverage):
		# Each metamodality will return a set of outcomes for its bound effects
		# That is, if the program has 3 effects, each metamodality will return 3 arrays
		# These then need to be combined into the overall program effect on the parameters
		# perhaps using the nonlinear saturating system
		# For coverage programs, the CO curve is the identity function and thus the units
		# are still normalized. De-normalization happens as a third step
		outcomes = []
		for mm,coverage in zip(self.metamodalities,effective_coverage):
			outcomes.append(mm.get_outcomes(self.modalities,coverage))

		# Indexing is outcomes[metamodality][effect][time]
		# Note that outcomes is a list of lists, because the metamodality returns a list of outputs
		# rather than a matrix
		# What we want is outcomes[effect][time]
		# Now we need to merge all of the entries of outcomes into a single outcome. This is done on a per-effect basis

		output_outcomes = []

		for i in xrange(0,len(self.effects['param'])): # For each output effect
			# In this loop, we iterate over the metamodalities and then combine the outcome into a single parameter
			# that is returned for use in D.M
			tmp = outcomes[0][i]
			if len(outcomes) > 1:
				for j in xrange(1,len(outcomes)): # For each metamodality
					tmp += outcomes[j][i]
			tmp *= (1/len(outcomes))
			output_outcomes.append(tmp)
		#print output_outcomes
		return output_outcomes

	def convert_units(self,output_outcomes,sim_output):
		# This function takes in a set of outcomes (generated by this program) and
		# simobject output e.g. sim_output = sim.run()
		# It iterates over the modalities to find coverage-type modalities
		# It then uses the population sizes in sim_output to convert nondimensional 
		# coverage into numbers of people

		return output_outcomes


	def add_modality(self,name,cc_data={'function':'null','parameters':None},co_data = [{'function':'null','parameters':None}],nonhivdalys=0):
		new_modality = Modality(name,cc_data,co_data,nonhivdalys,maxcoverage=1.0)
		self.modalities.append(new_modality)
		# Synchronize metamodalities
		# Add a new metamodality with all of the previous ones
		current_metamodalities = len(self.metamodalities)
		for i in xrange(0,current_metamodalities):
			self.metamodalities.append(Metamodality([new_modality],metamodality=self.metamodalities[i]))
		self.metamodalities.append(Metamodality([new_modality]))

		return new_modality

	def remove_modality(self,name,uuid):
		raise Exception('Not fully implemented yet!')
		idx = 1 # Actually look up the modality by name or by uuid
		m = self.modalities.pop(idx)
		return m


class MetaProgram(object):
	# A metaprogram corresponds to an overlap of programs
	
	# The metamodality knows the coverage (number of people) who fall into the overlapping category
	# The amount of overlap still needs to be specified though
	# For example, if the population size is 100 people, and modality 1 reaches 40, and modality 2 reaches 20,
	# and the metamodality reaches 10, then we know that 10 people are reached by both - 50% of modality 2, and 25% of modality 1
	# So the metamodality coverage is a fraction of the total population
	# And it must be smaller than the smallest coverage for the individual modalities
	def __init__(self,modalities,method='maximum',metamodality=None,overlap=None): # where m1 and m2 are Modality instances
		self.modalities = [m.uuid for m in modalities]

		if metamodality is not None:
			self.modalities += metamodality.modalities # Append the UUIDs from the previous metamodality object

		self.temp_coverage = 0 # This is used internally by program.get_coverage()
		self.method = method

	def get_outcomes(self,modalities,effective_coverage):
		outcomes = []
		for m in modalities:
			if m.uuid in self.modalities:
				outcomes.append(m.get_outcomes(effective_coverage))

		#print 'METAMODALITY'
		# It is indexed
		# outcomes[modality][effect][time]
		# The modality returns an set of outcomes (an array of arrays)
		# Now we need to iterate over them to get a single outcome from the metamodality

		# Suppose the effective_coverage is 0.3. That means that 30% of the population is covered by 
		# ALL of the programs associated with this metamodality. The final outcome can be 
		# combined in different ways depending on the method selected here
		final_outcomes = []
		for i in xrange(0,len(outcomes[0])): # For each output effect
			# In this loop, we iterate over the modalities and then combine the outcome into a single parameter
			# that is returned for use in D.M
			# Each element in outcomes corresponds to 
			tmp = [x[i] for x in outcomes] # These are the outcomes for effect i for each modality
			# tmp is a list of tmp[modality][outcome] for fixed effect. Now we have to iterate over tmp
			if self.method == 'maximum':
				out = tmp[0]
				for j in xrange(1,len(tmp)):
					out = maximum(out,tmp[j]) # use maximum function from numpy
			final_outcomes.append(out)

		#print final_outcomes
		# Indexing is final_outcomes[effect][time]
		return final_outcomes


	def get_coverage(self,modalities,coverage):
		# Return a list of all of the coverages corresponding to the modalities
		# referred to by this metamodality instance
		# There is one coverage for each modality

		# Note that internally, the coverages are divided equally
		# For example, if the population size is 100 people, and modality 1 is capable of reaching 40, and modality 2 is capable of reaching 20,
		# and the metamodality reaches 10, then we know that 10 people are reached by both. So we set the metamodality maxcoverage
		# to 10 people (0.1). 
		# Now, suppose modality 1 reaches 20 people, and modality 2 reaches 20 people. This mean that of the metamodality now reaches 5 people
		# So we have
		# metamodalitycoverage = (m_1_actualcoverage/m_1_max*m_2_actualcoverage/m_2_max)*self.maxcoverage
		# is the fraction of the total population reached by this combination of programs
		actual_coverage = self.maxcoverage
		for i in xrange(0,len(modalities)):
			if modalities[i].uuid in self.modalities:
				actual_coverage *= coverage[i]/modalities[i].maxcoverage
		return actual_coverage

	def __repr__(self):
		return '(%s)' % (','.join([s[0:4] for s in self.modalities]))

class Program(object):
	# This class is a single modality - a single thing that 
	def __init__(self,name,cc_inputs,co_inputs,nonhivdalys):
		# THINGS THAT PROGRAMS HAVE
		# frontend quantities
		# functions
		# conversion from FE parameters to BE parameters

		# EXAMPLE INPUTS
		# cc_inputs[0] = {}
		# cc_inputs[0]['pop'] = 'FSW'
		# cc_inputs[0]['form'] = 'cc_scaleup'
		# cc_inputs[0]['fe_params'] = {u'coveragelower': 0.2, u'nonhivdalys': 0.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.75, u'scaleup': 0.73}

		# co_inputs[0] = {}
		# co_inputs[0]['pop'] = 'FSW'
		# co_inputs[0]['param'] = 'hivtest'
		# co_inputs[0]['form'] = 'co_cofun'
		# co_inputs[0]['fe_params'] = [0, 0, 2, 2]

		self.name = name		
		self.nonhivdalys = nonhivdalys
		self.uuid = str(uuid.uuid4())

		assert(set([x['pop'] for x in cc_inputs]) == set([x['pop'] for x in co_inputs])) # A CC curve must be defined for every population that this program affects

		self.cost_coverage = defaultdict(list)
		for cc in cc_inputs:
			cc_class = getattr(ccocs, cc['form']) # This is the class corresponding to the CC form e.g. it could be  a <ccocs.cc_scaleup> object
			assert(cc['pop'] not in self.cost_coverage.keys()) # Each program can only have one CC curve per population
			self.cost_coverage[cc['pop']] = cc_class(cc['fe_params']) # Instantiate it with the CC data, and append it to the program's CC array

		self.coverage_outcome = defaultdict(dict)
		for co in co_inputs:
			co_class = getattr(ccocs, co['form'])
			if isinstance(co['param'],list): # Note that lists cannot be dictionary keys, so [u'condom', u'com'] -> 'condom-com'
				co['param'] = '-'.join(co['param'])
			assert(co['pop'] not in self.coverage_outcome.keys() or co['param'] not in self.coverage_outcome[co['pop']].keys()) # Each program can only have one CO curve per effect
			self.coverage_outcome[co['pop']][co['param']] = cc_class(cc['fe_params']) # Instantiate it with the CC data, and append it to the program's CC array


	def get_effects(self):
		# Returns a list of tuples storing effects as (population,parameter)
		

		# A set of effects - each effect has a population
		# Each population has a coverage
		# Need to be able to generate a list of effects easily
		# And a list of populations easily
		return

	def get_coverage(self,spending,pop):
		# Return the coverage of a particular population given the spending amount
		return self.cost_coverage[cc['pop']].evaluate(spending)

	def get_outcome(self,coverage,pop,effect):
		# Return the outcome for a particular effect given the parent population's coverage
		if isinstance(effect,list):
			effect = '-'.join(effect)
		return self.coverage_outcome[pop][effect].evaluate(coverage)

	def __repr__(self):
		return 'Program %s (%s)' % (self.uuid[0:4],self.name)

