import uuid
from operator import mul
import defaults

from math import log
from numpy import linspace, exp, isnan, multiply, arange, mean, array, maximum
from numpy import log as nplog


class Program:
	def __init__(self,name,full_name = None,category = 'None'):
		self.name = name
		if full_name is None:
			self.full_name = name
		else:
			self.full_name = full_name
		self.category = category
		self.uuid = str(uuid.uuid4())

		self.modalities = []
		self.metamodalities = [] # One metamodality for every combination of modalities, including single modalities
		self.effective_coverage = [] # An effective coverage for every metamodality

		self.reachability_interaction = 'random' # These are the options on slide 7 of the proposal
		# The reachability interaction enables the metamodality maxcoverage to be automatically set

		# This stores the list of effects. Each modality and metamodality must contain a coverage-outcome
		# curve for each effect in the Program
		# May require effects as an argument to the constructor later?
		self.effects = {}
		self.effects['paramtype'] = []
		self.effects['popname'] = []
		self.effects['param'] = []
		self.effects['iscoverageparam'] = []

	@classmethod
	def import_legacy(Program,programdata):
		# Take in D['programs'][i] and return a corresponding Program instance
		p = Program(programdata['name'])

		p.effects['paramtype'] = [x['paramtype'] for x in programdata['effects']]
		p.effects['popname'] = [x['popname'] for x in programdata['effects']]
		p.effects['param'] = [x['param'] for x in programdata['effects']]
		p.effects['iscoverageparam'] = [x['param'] in ['numost','numpmtct','numfirstline','numsecondline'] for x in programdata['effects']]

		# Legacy programs only have one modality
		# Some complete programs have only one spending_only modality
		if len(programdata['effects']) == 0:
			m = p.add_modality(p.name)
			return p

		cc_data = {}
		cc_data['function'] = 'cceqn'

		# Workaround for coverage programs
		if 'coparams' not in programdata['effects'][0].keys():
			cc_data['function'] = 'cc2eqn' # OST etc. use cc2eqn
		else:
			cc_data['function'] = 'cceqn'
		cc_data['parameters'] = programdata['ccparams']

		co_data = []
		# Take care here - the effects should probably be added to all of the modalities in the same order
		# That is, they should be in the same order as the program effects
		for effect in programdata['effects']:
			this_co = {}
			if 'coparams' not in effect.keys():
				this_co['function'] = 'identity'
				this_co['parameters'] = None
			else:
				this_co['function'] = 'coeqn'
				this_co['parameters'] = effect['coparams']
			co_data.append(this_co)
		m = p.add_modality(p.name,cc_data,co_data,programdata['nonhivdalys'])
		return p

	def get_coverage(self,spending):
		# This function returns an array of effective coverage values for each metamodality
		# reflow_metamodalities should generally be run before this function is called
		# this is meant to happen automatically when add_modality() or remove_modality is called()
		if len(self.modalities) == 1:
			spending = array([[spending]]) # Need a better solution...

		assert(len(spending)==len(self.modalities))

		# First, get the coverage for each modality
		coverage = []
		for i in xrange(0,len(spending)):
			coverage.append(self.modalities[i].get_coverage(spending[i,:]))

		# Next, calculate the coverage for each metamodality
		effective_coverage = []
		for mm in self.metamodalities:
			effective_coverage.append(mm.get_coverage(self.modalities,coverage))

		# Return the metamodality coverage
		return effective_coverage

	def get_outcomes(self,effective_coverage):
		# Each metamodality will return a set of outcomes for its bound effects
		# That is, if the program has 3 effects, each metamodality will return 3 arrays
		# These then need to be combined into the overall program effect on the parameters
		# perhaps using the nonlinear saturating system
		# NOTE - an outcome IS a parameter value
		outcomes = []
		for mm,coverage in zip(self.metamodalities,effective_coverage):
			outcomes.append(mm.get_outcomes(self.modalities,coverage))

		# Note that outcomes is a list of lists, because the metamodality returns a list of outputs
		# rather than a matrix
		# Now we need to merge all of the entries of outcomes into a single outcome. This is done on a per-effect basis

		final_outcomes = []
		#print outcomes
		#print len(self.effects['param'])
		for i in xrange(0,len(self.effects['param'])): # For each output effect
			# In this loop, we iterate over the metamodalities and then combine the outcome into a single parameter
			# that is returned for use in D.M
			tmp = outcomes[0][i]
			for j in xrange(0,len(outcomes)): # For each metamodality
				tmp += outcomes[j][i]
			tmp *= (1/len(outcomes))
			final_outcomes.append(tmp)
		return final_outcomes

	def add_modality(self,name,ccparams=None,coparams=None,nonhivdalys=0):
		if ccparams is None:
			ccparams = defaults.program['ccparams']
		if coparams is None:
			coparams = defaults.program['coparams']

		new_modality = Modality(name,ccparams,coparams,nonhivdalys,maxcoverage=1.0)
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
			
			# print 'MODALITIES'
			# print [m.maxcoverage for m in self.modalities]
			# print 'BEFORE'
			# print [mm.maxcoverage for mm in self.metamodalities]
			# print sum([mm.maxcoverage for mm in self.metamodalities])
			# Now we go through the subsets - basically, if metamodality 1 is a subset of metamodality 2, then we subtract metamodality 2's coverage from metamodality 1
			for i in xrange(len(self.modalities),0,-1): # Iterate over metamodalities containing i modalities
				superset = [mm for mm in self.metamodalities if len(mm.modalities) >= i]
				subset = [mm for mm in self.metamodalities if len(mm.modalities) == i-1]


				for sub in subset:
					for sup in superset: 
						if set(sub.modalities).issubset(set(sup.modalities)):
							sub.maxcoverage -= sup.maxcoverage

			# print 'AFTER'
			# print [mm.maxcoverage for mm in self.metamodalities]
			# print sum([mm.maxcoverage for mm in self.metamodalities])
			# The above sum should be <= 1, otherwise double-counting is definitely occuring
			# print '----'


class Metamodality:
	# The metamodality knows the coverage (number of people) who fall into the overlapping category
	# The amount of overlap still needs to be specified though
	# For example, if the population size is 100 people, and modality 1 reaches 40, and modality 2 reaches 20,
	# and the metamodality reaches 10, then we know that 10 people are reached by both - 50% of modality 2, and 25% of modality 1
	# So the metamodality coverage is a fraction of the total population
	# And it must be smaller than the smallest coverage for the individual modalities
	def __init__(self,modalities,method='maximum',metamodality=None,overlap=None): # where m1 and m2 are Modality instances
		self.modalities = [m.uuid for m in modalities]

		# The reason for storing self.maxcoverage here is because it might be over-ridden
		# manually by users in the future. This is the quantity that defines the extent to which
		# the modalities overlap 
		self.maxcoverage = min([m.maxcoverage for m in modalities]) # Default upper bound on fractional coverage of the total population
		


		if metamodality is not None:
			self.modalities += metamodality.modalities # Append the UUIDs from the previous metamodality object

		# We do not store weakrefs here because conversion from class to dict
		# may be frequent here, and it could become expensive if the references
		# are regenerated too frequently

		self.method = method

	def get_outcomes(self,modalities,effective_coverage):
		outcomes = []
		for m in modalities:
			if m.uuid in self.modalities:
				outcomes.append(m.get_outcomes(effective_coverage))

		# The modality returns an set of outcomes (an array of arrays)
		# Now we need to iterate over them to get a single outcome from the metamodality

		# Suppose the effective_coverage is 0.3. That means that 30% of the population is covered by 
		# ALL of the programs associated with this metamodality. The final outcome can be 
		# combined in different ways depending on the method selected here
		final_outcomes = []
		for i in xrange(0,len(outcomes[0])): # For each output effect
			# In this loop, we iterate over the modalities and then combine the outcome into a single parameter
			# that is returned for use in D.M
			tmp = [x[i] for x in outcomes] # These are the outcomes for effect i for each modality
			if self.method == 'maximum':
				out = tmp[0]
				for j in xrange(1,len(tmp)):
					out = maximum(out,tmp[j]) # use maximum function from numpy
			final_outcomes.append(out)

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

class Modality:
	def __init__(self,name,cc_data= None,co_data = None,nonhivdalys = None, maxcoverage = 1.0):
		# Note - cc_data and co_data store the things which the user enters into the frontend
		# The functions take in convertedcc_data and convertedco_data, which are stored internally
		self.name = name

		if cc_data is None:
			self.spending_only = True
		else:
			self.spending_only = False

		# This variable may be removed in future once the algorithm/calculations are more finalized
		# This is because the maxcoverage can also be accounted for in the ccfun()
		# For now, self.maxcoverage scales the total coverage and helps to work out the metamodality coverage
		self.maxcoverage = maxcoverage # The maximum fraction of the total population that this modality can reach

		# Cost-Coverage - the modality contains one
		self.cc_data = cc_data
		if cc_data['function'] == 'cc2eqn':
			self.ccfun = cc2eqn
		else:
			self.ccfun = cceqn

		# Coverage-outcome - the modality contains one for each program effect
		self.co_data = co_data
		self.cofun = []
		for co in self.co_data:
			if co['function'] == 'coeqn':
				self.cofun.append(coeqn)
			elif co['function'] == 'identity':
				self.cofun = identity

		self.nonhivdalys = nonhivdalys
		self.uuid = str(uuid.uuid4())

	def get_coverage(self,spending):
		# self.cc_data['function'] is one of the keys in self.ccfun
		# self.cc_data['parameters'] contains whatever is required by the curve function
		convertedccparams = self.get_convertedccparams()
		cc_arg = convertedccparams[0] # Apply random perturbation here
		print cc_arg
		print self.name
		return self.ccfun(spending,cc_arg)

	def get_outcomes(self,coverage):
		# Calculate all of the outcomes for this modality as a function of modality coverage
		outcomes = []
		for i in xrange(0,len(self.co_data)):
			convertedcoparams = self.get_convertedcoparams(self.co_data[i])
			co_arg = convertedcoparams[0] # Apply random perturbation here
			outcomes.append(self.cofun[i](coverage,co_arg))
		print outcomes
		return outcomes 

	def get_convertedccparams(self):
	    ''' Convert GUI inputs into the form needed for the calculations '''
	    # Essentially, the GUI contains boxes for the user to enter information about
	    # the curves. This information is used to construct the parameters for
	    # the actual curve functions
	    ccparams = self.cc_data['parameters']
	    convertedccparams = []

	    # Construct the convertedccparams depending on which functional form is being used
	    if self.cc_data['function'] == 'cceqn':

		    if 'scaleup' in ccparams and ccparams['scaleup'] and ~isnan(ccparams['scaleup']):
		        growthratel = exp((1-ccparams['scaleup'])*log(ccparams['saturation']/ccparams['coveragelower']-1)+log(ccparams['funding']))
		        growthratem = exp((1-ccparams['scaleup'])*log(ccparams['saturation']/((ccparams['coveragelower']+ccparams['coverageupper'])/2)-1)+log(ccparams['funding']))
		        growthrateu = exp((1-ccparams['scaleup'])*log(ccparams['saturation']/ccparams['coverageupper']-1)+log(ccparams['funding']))
		        convertedccparams = [[ccparams['saturation'], growthratem, ccparams['scaleup']], [ccparams['saturation'], growthratel, ccparams['scaleup']], [ccparams['saturation'], growthrateu, ccparams['scaleup']]]
		    else:
		        growthratel = (-1/ccparams['funding'])*log((2*ccparams['saturation'])/(ccparams['coveragelower']+ccparams['saturation']) - 1)        
		        growthratem = (-1/ccparams['funding'])*log((2*ccparams['saturation'])/(((ccparams['coveragelower']+ccparams['coverageupper'])/2)+ccparams['saturation']) - 1)        
		        growthrateu = (-1/ccparams['funding'])*log((2*ccparams['saturation'])/(ccparams['coverageupper']+ccparams['saturation']) - 1)        
		        convertedccparams = [[ccparams['saturation'], growthratem], [ccparams['saturation'], growthratel], [ccparams['saturation'], growthrateu]]
		                    
		    return convertedccparams

	def get_convertedcoparams(self,co_data):
		# Copied from makeccocs.makecosampleparams()
		# Convert the co_data into parameter values for co_fun
		# Naturally, this conversion depends on the functional form of co_fun
		coparams = co_data['parameters']
		if co_data['function'] == 'coeqn':
			muz, stdevz = (coparams[0]+coparams[1])/2, (coparams[1]-coparams[0])/6 # Mean and standard deviation calcs
			muf, stdevf = (coparams[2]+coparams[3])/2, (coparams[3]-coparams[2])/6 # Mean and standard deviation calcs
			convertedcoparams = [muz, stdevz, muf, stdevf]
			convertedcoparams = [[muz,muf],[muz,muf],[muz,muf]] # DEBUG CODE, DO THIS PROPERLY LATER
		elif co_data['function'] == 'identity':
			convertedcoparams = None # No parameters required
		return convertedcoparams

	def __repr__(self):
		return '%s (%s)' % (self.name,self.uuid[0:4])



# --------------------------- functional forms for the CCOCs

def identity(x,params):
	return x

def linear(x,params):
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

def cceqn(x, p, eps=1e-3):
    '''
    3-parameter equation defining cost-coverage curve.
    x is total cost, p is a list of parameters (of length 3):
        p[0] = saturation
        p[1] = inflection point
        p[2] = growth rate... 
    Returns y which is coverage.
    '''
    y = p[0] / (1 + exp((log(p[1])-nplog(x))/max(1-p[2],eps)))

    return y

def cco2eqn(x, p):
    '''
    4-parameter equation defining cost-outcome curves.
    x is total cost, p is a list of parameters (of length 2):
        p[0] = saturation
        p[1] = growth rate
        p[2] = outcome at zero coverage
        p[3] = outcome at full coverage
    Returns y which is coverage.'''
    y = (p[3]-p[2]) * (2*p[0] / (1 + exp(-p[1]*x)) - p[0]) + p[2]
    return y

def cc2eqn(x, p):
    '''
    2-parameter equation defining cc curves.
    x is total cost, p is a list of parameters (of length 2):
        p[0] = saturation
        p[1] = growth rate
    Returns y which is coverage. '''
    y =  2*p[0] / (1 + exp(-p[1]*x)) - p[0]
    return y