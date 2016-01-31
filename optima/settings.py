"""
SETTINGS

Store all the static data for a project that won't change except between Optima versions.

How verbose works:
  0 = no output except absolutely critical
  1 = serious warnings/errors only
  2 = standard output -- fair amount of detail
  3 = additional detail
  4 = absolutely everything

Version: 2016jan29
"""

from numpy import arange, array, concatenate as cat, linspace, shape
from optima import OptimaException, defaultrepr, printv, dcp


class Settings():
    def __init__(self):
        self.dt = 0.2 # Timestep
        self.start = 2000.0 # Default start year
        self.end = 2030.0 # Default end year
        self.hivstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'lt50']
        self.healthstates = ['uncirc', 'circ', 'undx', 'dx', 'care', 'usvl', 'svl', 'lost', 'off']
        self.ncd4 = len(self.hivstates)
        
        # Health states by diagnosis
        self.uncirc = arange(0,1) # Uninfected, uncircumcised
        self.circ   = arange(1,2) # Uninfected, circumcised
        self.undx   = arange(0*self.ncd4+2, 1*self.ncd4+2) # Infected, undiagnosed
        self.dx     = arange(1*self.ncd4+2, 2*self.ncd4+2) # Infected, diagnosed
        self.care   = arange(2*self.ncd4+2, 3*self.ncd4+2) # Infected, in care 
        self.usvl   = arange(3*self.ncd4+2, 4*self.ncd4+2) # Infected, on treatment, with unsuppressed viral load
        self.svl    = arange(4*self.ncd4+2, 5*self.ncd4+2) # Infected, on treatment, with suppressed viral load
        self.lost   = arange(5*self.ncd4+2, 6*self.ncd4+2) # Infected, but lost to follow-up
        self.off    = arange(6*self.ncd4+2, 7*self.ncd4+2) # Infected, previously on treatment, off ART, but still in care
		
       	
        # Health states by CD4 count
        spacing = array([0,1,2])*self.ncd4 
        self.acute = 2 + spacing
        self.gt500 = 3 + spacing
        self.gt350 = 4 + spacing
        self.gt200 = 5 + spacing
        self.gt50  = 6 + spacing
        self.lt50  = 7 + spacing

        # Combined states
        self.sus       = cat([self.uncirc, self.circ]) # All uninfected
        self.alldx     = cat([self.dx, self.care, self.usvl, self.svl, self.lost, self.off]) # All people diagnosed
        self.allcare   = cat([self.care, self.usvl, self.svl,self.off]) # All people in care
        self.allplhiv  = cat([self.undx, self.alldx]) # All PLHIV
        self.alltx     = cat([self.usvl, self.svl]) # All people on treatment
        self.allstates = cat([self.sus, self.allplhiv]) # All states
        self.nstates   = len(self.allstates) # Total number of states
        
        # Set labels for each health state
        thesestates = dcp(self.healthstates)
        self.statelabels = []
        for thisstate in thesestates:
            n = len(getattr(self, thisstate))
            if n==1: self.statelabels.append(thisstate)
            elif n==self.ncd4:
                for hivstate in self.hivstates: 
                    self.statelabels.append(thisstate+'-'+hivstate)
            else:
                errormsg = 'Cannot understand health state "%s": length %i, expecting 1 or %i' % (thisstate, n, self.ncd4)
                raise OptimaException(errormsg)
        if len(self.statelabels)!=self.nstates:
            errormsg = 'Incorrect number of health states provided (actually %i, want %i)' % (len(self.statelabels), self.nstates)
            raise OptimaException(errormsg)
        
        # Non-cascade settings/states
        self.usecascade = False # Whether or not to actually use the cascade
        self.tx  = self.svl # Infected, on treatment -- not used with the cascade
        
        # Other
        self.optimablue = (0.16, 0.67, 0.94) # The color of Optima
        self.verbose = 2 # Default verbosity for how much to print out -- see definitions in utils.py:printv()
        self.safetymargin = 0.5 # Do not move more than this fraction of people on a single timestep
        printv('Initialized settings', 4, self.verbose) # And show how verbose is used
    
    
    def __repr__(self):
        ''' Prettily print object '''
        output =  defaultrepr(self)
        return output
    
    
    def maketvec(self, start=None, end=None, dt=None):
        ''' Little function for calculating the time vector -- here since start, end, dt are stored here '''
        printv('Making time vector', 4, self.verbose)
        if start is None: start=self.start
        if end is None: end=self.end
        if dt is None: dt=self.dt
        tvec = linspace(start, end, round((end-start)/dt)+1)
        return tvec
    
    
    def convertlimits(self, limits=None, tvec=None, dt=None, safetymargin=None, verbose=None):
        ''' Link to function below '''
        return convertlimits(settings=self, limits=limits, tvec=None, dt=dt, safetymargin=None, verbose=verbose)





def gettvecdt(tvec=None, dt=None, justdt=False):
    ''' 
    Function to encapsulate the logic of returning sensible tvec and dt based on flexible input.
    
    If tvec and dt are both supplied, do nothing.
    
    Will always work if tvec is not None, but will use default value for dt if dt==None and len(tvec)==1.
    
    Usage:
        tvec,dt = gettvecdt(tvec, dt)
    
    Version: 2016jan30
    '''
    defaultdt = 0.2 # WARNING, slightly dangerous to hard-code but should be ok, since very rare situation
    if tvec is None: 
        if justdt: return defaultdt # If it's a constant, maybe don' need a time vector, and just return dt
        else: raise OptimaException('No time vector supplied, and unable to figure it out') # Usual case, crash
    elif isinstance(tvec, (int, float)): tvec = array([tvec]) # Convert to 1-element array
    elif shape(tvec): # Make sure it has a length -- if so, overwrite dt
        if len(tvec)>=2: dt = tvec[1]-tvec[0] # Even if dt supplied, recalculate it from the time vector
        elif dt is None: dt = defaultdt # Or give up and use default
        else: dt = dt # Use input
    else:
        raise OptimaException('Could not understand tvec of type "%s"' % type(tvec))
    return tvec, dt
    
    

    
def convertlimits(limits=None, tvec=None, dt=None, safetymargin=None, settings=None, verbose=None):
    ''' 
    Method to calculate numerical limits from qualitative strings.
    
    Valid usages:
        convertlimits() # Returns dict of max rates that can be called later
        convertlimits('maxrate') # Returns maxrate = 0.9/dt, e.g. 4
        convertlimits([0, 'maxrate']) # Returns e.g. [0, 4]
        convertlimits(4) # Returns 4
    
    Version: 2016jan30
    '''
    if verbose is None:
        if settings is not None: verbose = settings.verbose
        else: verbose=2
    
    printv('Converting to numerical limits...', 4, verbose)
    if dt is None: 
        if settings is not None: dt = settings.dt
        else: raise OptimaException('convertlimits() must be given either a timestep or a settings object')
    if safetymargin is None:
        if settings is not None: safetymargin = settings.safetymargin
        else: 
            printv('Note, using default safetymargin since could not find it', 4, verbose)
            safetymargin = 0.8 # Not that important, so just set safety margin
    
    # Update dt 
    dt = gettvecdt(tvec=tvec, dt=dt, justdt=True)
    
    # Actually define the rates
    maxrate = safetymargin/dt
    maxpopsize = 1e9
    maxmeta = 1000.0
    maxacts = 5000.0
    
    # It's a single number: just return it
    if isinstance(limits, (int, float)): return limits
    
    # Just return the limits themselves as a dict if no input argument
    if limits is None: 
        return {'maxrate':maxrate, 'maxpopsize':maxpopsize, 'maxmeta':maxmeta, 'maxacts':maxacts}
    
    # If it's a string, convert to list, but remember this
    isstring = (type(limits)==str)
    if isstring: limits = [limits] # Convert to list
    
    # If it's a tuple, convert to a list before converting back at the end
    istuple = (type(limits)==tuple)
    if istuple: limits = list(limits)
    
    # If list argument is given, replace text labels with numeric limits
    for i,m in enumerate(limits):
        if m=='maxrate': limits[i] = maxrate
        elif m=='maxpopsize': limits[i] = maxpopsize
        elif m=='maxmeta': limits[i] = maxmeta
        elif m=='maxacts': limits[i] = maxacts
        else: limits[i] = limits[i] # This leaves limits[i] untouched if it's a number or something
    
    # Wrap up
    if isstring: return limits[0] # Return just a scalar
    if istuple: return tuple(limits) # Convert back to a tuple
    else: return limits # Or return the whole list