import abc
from math import log
from numpy import linspace, exp, isnan, multiply, arange, mean, array, maximum
from numpy import log as nplog

class ccoc(object):
	# A ccoc object has
	# - A set of frontend parameters
	# - A selected functional form for the curve
	# - A mapping function that converts the FE parameters into BE parameters
	# - The ability to perturb BE parameters prior to retrieving the output value
	__metaclass__ = abc.ABCMeta

	def __init__(self,fe_params):
		self.fe_params = fe_params

	@abc.abstractmethod # This method must be defined by the derived class
	def function(self,x,p):
		# This function takes in either a spending value or coverage
		# and the functional parameters for the object, and returns
		# the coverage or the outcome
		pass

	@abc.abstractmethod # This method must be defined by the derived class
	def convertparams(self,perturb=False):
		# Take the current frontend parameters, and convert them into backend parameters
		# that can be passed into ccoc.function()
		pass

	def evaluate(self,x):
		# Todo: incorporate perturbation
		p = self.convertparams()
		return self.function(x,p)

	def invert(self,y):
		p = self.convertparams()
		return self.inverse(y,p)

	def inverse(self,y,p):
		# This function should find the inverse numerically
		# but it can be overloaded by derived classes to provide
		# an analytic inverse
		raise Exception('Numerical inverse not implemented yet')

######## SPECIFIC CCOC IMPLEMENTATIONS

class cc_scaleup(ccoc):
	def function(self,x,p):
		return cceqn(x,p)

	def convertparams(self):
		growthratel = exp((1-self.fe_params['scaleup'])*log(self.fe_params['saturation']/self.fe_params['coveragelower']-1)+log(self.fe_params['funding']))
		growthratem = exp((1-self.fe_params['scaleup'])*log(self.fe_params['saturation']/((self.fe_params['coveragelower']+self.fe_params['coverageupper'])/2)-1)+log(self.fe_params['funding']))
		growthrateu = exp((1-self.fe_params['scaleup'])*log(self.fe_params['saturation']/self.fe_params['coverageupper']-1)+log(self.fe_params['funding']))
		convertedccparams = [[self.fe_params['saturation'], growthratem, self.fe_params['scaleup']], [self.fe_params['saturation'], growthratel, self.fe_params['scaleup']], [self.fe_params['saturation'], growthrateu, self.fe_params['scaleup']]]
		return convertedccparams[0] # TODO: This is currently only returning the unperturbed case

class cc_noscaleup(ccoc):
	def function(self,x,p):
		return cc2eqn(x,p)

	def convertparams(self):
		growthratel = (-1/self.fe_params['funding'])*log((2*self.fe_params['saturation'])/(self.fe_params['coveragelower']+self.fe_params['saturation']) - 1)        
		growthratem = (-1/self.fe_params['funding'])*log((2*self.fe_params['saturation'])/(((self.fe_params['coveragelower']+self.fe_params['coverageupper'])/2)+self.fe_params['saturation']) - 1)        
		growthrateu = (-1/self.fe_params['funding'])*log((2*self.fe_params['saturation'])/(self.fe_params['coverageupper']+self.fe_params['saturation']) - 1)        
		convertedccparams = [[self.fe_params['saturation'], growthratem], [self.fe_params['saturation'], growthratel], [self.fe_params['saturation'], growthrateu]]
		return convertedccparams[0] # TODO: This is currently only returning the unperturbed case

class co_cofun(ccoc):
	def function(self,x,p):
		return coeqn(x,p)

	def inverse(self,y,p):
		return (y-p[0])/(p[1]-p[0]) 
		
	def convertparams(self):
		muz, stdevz = (self.fe_params[0]+self.fe_params[1])/2, (self.fe_params[1]-self.fe_params[0])/6 # Mean and standard deviation calcs
		muf, stdevf = (self.fe_params[2]+self.fe_params[3])/2, (self.fe_params[3]-self.fe_params[2])/6 # Mean and standard deviation calcs
		convertedcoparams = [muz, stdevz, muf, stdevf]
		convertedcoparams = [[muz,muf],[muz,muf],[muz,muf]] # DEBUG CODE, DO THIS PROPERLY LATER
		return convertedcoparams[0] # TODO: This is currently only returning the unperturbed case

class co_linear(ccoc):
	def function(self,x,p):
		return linear(x,p)

	def convertparams(self):
		return self.fe_params

class identity(ccoc):
	def function(self,x,p):
		return x

	def convertparams(self):
		return None

class null(ccoc):
	def function(self,x,p):
		return None

	def convertparams(self):
		return None

############## FUNCTIONAL FORMS COPIED FROM makeccocs.py ##############
def linear(x,params):
	return params[0]*x+params[1]

def cc2eqn(x, p):
    '''
    2-parameter equation defining cc curves.
    x is total cost, p is a list of parameters (of length 2):
        p[0] = saturation
        p[1] = growth rate
    Returns y which is coverage. '''
    y =  2*p[0] / (1 + exp(-p[1]*x)) - p[0]
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