import uuid
from operator import mul

class Program:
	def __init__(self,name):
		self.name = name
		self.uuid = str(uuid.uuid4())

		self.modalities = []
		self.metamodalities = [] # One metamodality for every combination of modalities, including single modalities
		self.effective_coverage = [] # An effective coverage for every metamodality

		self.reachability_interaction = 'random' # These are the options on slide 7 of the proposal
		# The reachability interaction enables the metamodality maxcoverage to be automatically set

	def calculate_effective_coverage(self,spending):
		# This function returns an array of effective coverage values for each metamodality
		# reflow_metamodalities should generally be run before this function is called
		# this is meant to happen automatically when add_modality() or remove_modality is called()
		assert(len(spending)==len(self.modalities))

		coverage = []
		for i in xrange(0,len(spending)):
			coverage.append(self.modalities[i].get_coverage(spending[i]))

		effective_coverage = []
		for mm in self.metamodalities:
			effective_coverage.append(mm.get_coverage(self.modalities,coverage))

		return effective_coverage

	def add_modality(self,name,maxcoverage=1.0):
		new_modality = Modality(name,maxcoverage)
		self.modalities.append(new_modality)
		# Synchronize metamodalities
		# Add a new metamodality with all of the previous ones
		current_metamodalities = len(self.metamodalities)
		for i in xrange(0,current_metamodalities):
			self.metamodalities.append(Metamodality([new_modality],metamodality=self.metamodalities[i]))
		self.metamodalities.append(Metamodality([new_modality]))
		self.reflow_metamodalities()

		return new_modality

	def remove_modality(self,name,uuid):
		idx = 1 # Actually look up the modality by name or by uuid
		m = self.modalities.pop(idx)
		self.reflow_metamodalities()
		return m

	def reflow_metamodalities(self):
		# This function goes through and calculates the metamodality maxcoverage
		# and enforces no double counting (when reachability interaction is not additive)

		if self.reachability_interaction == 'random':
			# Random reachability means that if modality 1 is capable of reaching 40/100 people, and 
			# modality 2 is capable of reaching 20/100 people, then the probability of one person being reached
			# by both programs is (40/100)*(20/100)
			for mm in self.metamodalities:
				mm.maxcoverage = reduce(mul,[m.maxcoverage for m in self.modalities if m.uuid in mm.modalities]) # This is the total fraction reached
			
			print 'MODALITIES'
			print [m.maxcoverage for m in self.modalities]
			print 'BEFORE'
			print [mm.maxcoverage for mm in self.metamodalities]
			print sum([mm.maxcoverage for mm in self.metamodalities])
			# Now we go through the subsets - basically, if metamodality 1 is a subset of metamodality 2, then we subtract metamodality 2's coverage from metamodality 1
			for i in xrange(len(self.modalities),0,-1): # Iterate over metamodalities containing i modalities
				superset = [mm for mm in self.metamodalities if len(mm.modalities) >= i]
				subset = [mm for mm in self.metamodalities if len(mm.modalities) == i-1]


				for sub in subset:
					for sup in superset: 
						if set(sub.modalities).issubset(set(sup.modalities)):
							sub.maxcoverage -= sup.maxcoverage

			print 'AFTER'
			print [mm.maxcoverage for mm in self.metamodalities]
			print sum([mm.maxcoverage for mm in self.metamodalities])
			print '----'


class Metamodality:
	# The metamodality knows the coverage (number of people) who fall into the overlapping category
	# The amount of overlap still needs to be specified though
	# For example, if the population size is 100 people, and modality 1 reaches 40, and modality 2 reaches 20,
	# and the metamodality reaches 10, then we know that 10 people are reached by both - 50% of modality 2, and 25% of modality 1
	# So the metamodality coverage is a fraction of the total population
	# And it must be smaller than the smallest coverage for the individual modalities
	def __init__(self,modalities,method='maximum',metamodality=None,overlap=None): # where m1 and m2 are Modality instances
		self.modalities = [m.uuid for m in modalities]
		self.maxcoverage = min([m.maxcoverage for m in modalities]) # Default upper bound on fractional coverage of the total population
		


		if metamodality is not None:
			self.modalities += metamodality.modalities # Append the UUIDs from the previous metamodality object

		# We do not store weakrefs here because conversion from class to dict
		# may be frequent here, and it could become expensive if the references
		# are regenerated too frequently

		self.method = method

	def get_outcome(self,modalities,effective_coverage):
		outcomes = []
		for m in modalities:
			if m.uuid in self.modalities:
				outcomes.append(m.get_coverage(effective_coverage))

		# Suppose the effective_coverage is 0.3. That means that 30% of the population is covered by 
		# ALL of the programs associated with this metamodality. The final outcome can be 
		# combined in different ways depending on the method selected here
		if self.method == 'maximum': # Return the highest outcome as the total outcome
			return max(outcomes)

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

class Modality:
	def __init__(self,name,maxcoverage = 1.0):
		self.name = name

		self.maxcoverage = maxcoverage # The maximum fraction of the total population that this modality can reach

		# The number of people reached by this program is self.get_coverage(spending)*self.maxcoverage*population_size

		self.population = 'FSW' # Target population, must be present in the region
		self.parameter = 'testing' # Target parameter, must already exist in region metadata

		# Cost-Coverage
		self.ccfun = linear
		self.ccparams = {}
		self.ccparams['function'] = 'linear' # Use this dictionary to load/save
		self.ccparams['parameters'] = [0.5,0.0]
		
		# Coverage-outcome
		self.cofun = linear
		self.coparams = {}
		self.coparams['function'] = 'linear' # Use this dictionary to load/save
		self.coparams['parameters'] = [1.0,0.0]

		self.uuid = str(uuid.uuid4())

	def get_coverage(self,spending):
		# self.ccparams['function'] is one of the keys in self.ccfun
		# self.ccparams['parameters'] contains whatever is required by the curve function
		return self.ccfun(spending,self.ccparams['parameters'])

	def getoutcome(self,effective_coverage):
		return self.cofun(effective_coverage,self.coparams['parameters'])

	def __repr__(self):
		return '%s (%s)' % (self.name,self.uuid[0:4])

def linear(x,params,):
	return params[0]*x+params[1]

def sigmoid(x,params):
	return params[0]/exp((params[1]*(x-params[2])/params[3]))

def coeqn(x, p):
    '''
    Straight line equation defining coverage-outcome curve.
    x is coverage, p is a list of parameters (of length 2):
        p[0] = outcome at zero coverage
        p[1] = outcome at full coverage
    Returns y which is outcome.
    '''
    from numpy import array
    y = (p[1]-p[0]) * array(x) + p[0]

    return y
    
def ccoeqn(x, p):
    '''
    5-parameter equation defining cost-outcome curves.
    x is total cost, p is a list of parameters (of length 5):
        p[0] = saturation
        p[1] = inflection point
        p[2] = growth rate...
        p[3] = outcome at zero coverage
        p[4] = outcome at full coverage
    Returns y which is coverage.
    '''
    y = (p[4]-p[3]) * (p[0] / (1 + exp((log(p[1])-nplog(x))/(1-p[2])))) + p[3]

    return y
