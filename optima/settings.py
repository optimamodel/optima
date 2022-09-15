"""
SETTINGS

Store all the static data for a project that won't change except between Optima versions.

How verbose works:
  0 = no output except absolutely critical
  1 = serious warnings/errors only
  2 = standard output -- fair amount of detail
  3 = additional detail
  4 = absolutely everything

Version: 2016oct05
"""

from numpy import arange, array, concatenate as cat, shape
from optima import OptimaException, defaultrepr, printv, dcp, isnumber, inclusiverange


class Settings(object):
    def __init__(self, verbose=2):
        self.dt = 0.2 # Timestep
        self.start = 2000.0 # Default start year
        self.now = 2022.0 # Default current year
        self.dataend = 2030.0 # Default end year for data entry
        self.end = 2040.0 # Default end year for projections
        self.hivstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'lt50']
        self.healthstates = ['susreg', 'progcirc', 'undx', 'dx', 'care', 'lost', 'usvl', 'svl']
        self.ncd4 = len(self.hivstates)
        self.nhealth = len(self.healthstates)
        self.hivstatesfull = ['Acute infection', 'CD4>500', '350<CD4<500', '200<CD4<350', '50<CD4<200', 'CD4<50']
        self.healthstatesfull = ['Susceptible', 'Programmatically circumcised', 'Undiagnosed', 'Diagnosed', 'Linked to care', 'Lost to follow up', 'On unsuppressive ART', 'On suppressive ART']
        
        # Health states by diagnosis
        self.susreg   = arange(0,1) # Regular uninfected, may be uncircumcised
        self.progcirc = arange(1,2) # Uninfected, programatically circumcised
        self.undx     = arange(0*self.ncd4+2, 1*self.ncd4+2) # Infected, undiagnosed
        self.dx       = arange(1*self.ncd4+2, 2*self.ncd4+2) # Infected, diagnosed
        self.care     = arange(2*self.ncd4+2, 3*self.ncd4+2) # Infected, in care 
        self.lost     = arange(3*self.ncd4+2, 4*self.ncd4+2) # Infected, but lost to follow-up
        self.usvl     = arange(4*self.ncd4+2, 5*self.ncd4+2) # Infected, on treatment, with unsuppressed viral load
        self.svl      = arange(5*self.ncd4+2, 6*self.ncd4+2) # Infected, on treatment, with suppressed viral load
        self.notonart = cat([self.undx,self.dx,self.care,self.lost])
        self.dxnotincare = cat([self.dx,self.lost])

        self.nsus     = len(self.susreg) + len(self.progcirc)
        self.ninf     = self.nhealth - self.nsus
		
       	
        # Health states by CD4 count
        spacing = arange(self.ninf)*self.ncd4 
        self.acute = 2 + spacing
        self.gt500 = 3 + spacing
        self.gt350 = 4 + spacing
        self.gt200 = 5 + spacing
        self.gt50  = 6 + spacing
        self.lt50  = 7 + spacing
        self.aidsind = self.hivstates.index('gt50') # Find which state corresponds to AIDS...kind of ugly, I know

        # Combined states
        self.sus            = cat([self.susreg, self.progcirc]) # All uninfected
        self.alldx          = cat([self.dx, self.care, self.lost, self.usvl, self.svl]) # All people diagnosed
        self.allcare        = cat([         self.care,            self.usvl, self.svl]) # All people CURRENTLY in care
        self.allevercare    = cat([         self.care, self.lost, self.usvl, self.svl]) # All people EVER in care
        self.alltx          = cat([                    self.usvl, self.svl]) # All people on treatment
        self.allplhiv       = cat([self.undx, self.alldx]) # All PLHIV
        self.allaids        = cat([self.lt50, self.gt50]) # All people with AIDS
        self.allstates      = cat([self.sus, self.allplhiv]) # All states
        self.nstates        = len(self.allstates) # Total number of states

        # Infection methods
        self.inj = 0            # Injection, don't change number
        self.heterosexsex = 1   # Homosexual sexual transmission, don't change number
        self.homosexsex = 2     # Heterosexual sexual transmission, don't change number
        self.mtct = 3           # MTCT
        self.nmethods = 4       # 4 methods of transmission
        self.methodnames = ['Injection','Heterosexual sex','Homosexual sex','MTCT']

        self.advancedtracking = False # Try to always set to False to save time when running model
        
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
        
        
        # Other
        self.optimablue = (0.16, 0.67, 0.94) # The color of Optima
        self.verbose = verbose # Default verbosity for how much to print out -- see definitions in utils.py:printv()
        self.safetymargin = 0.5 # Do not move more than this fraction of people on a single timestep
        self.eps = 1e-3 # Must be small enough to be applied to prevalence, which might be ~0.1% or less
        self.infmoney = 1e10 # A lot of money
        printv('Initialized settings', 4, self.verbose) # And show how verbose is used
    
    
    def __repr__(self):
        ''' Prettily print object '''
        output =  defaultrepr(self)
        return output
    
    
    def maketvec(self, start=None, end=None, dt=None):
        ''' Little function for calculating the time vector -- here since start, end, dt are stored here '''
        printv('Making time vector', 4, self.verbose)
        if start is None: start=self.start
        if end   is None: end  =self.end
        if dt    is None: dt   =self.dt
        tvec = inclusiverange(start=start, stop=end, step=dt) # Can't use arange since handles floating point arithmetic badly, e.g. compare arange(2000, 2020, 0.2) with arange(2000, 2020.2, 0.2)
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
    elif isnumber(tvec): tvec = array([tvec]) # Convert to 1-element array
    elif shape(tvec): # Make sure it has a length -- if so, overwrite dt
        if len(tvec)>=2: dt = tvec[1]-tvec[0] # Even if dt supplied, recalculate it from the time vector
        else: dt = dt # Use input
    else:
        raise OptimaException('Could not understand tvec of type "%s"' % type(tvec))
    if dt is None: dt = defaultdt # Or give up and use default
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
    maxduration = 1000.
    maxmeta = 1000.0
    maxacts = 5000.0
    maxyear = settings.end if settings is not None else 2030. # Set to a default maximum year
    
    # It's a single number: just return it
    if isnumber(limits): return limits
    
    # Just return the limits themselves as a dict if no input argument
    if limits is None: 
        return {'maxrate':maxrate, 'maxpopsize':maxpopsize, 'maxduration':maxduration, 'maxmeta':maxmeta, 'maxacts':maxacts, 'maxyear':maxyear}
    
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
        elif m=='maxduration': limits[i] = maxduration
        elif m=='maxmeta': limits[i] = maxmeta
        elif m=='maxacts': limits[i] = maxacts
        elif m=='maxyear': limits[i] = maxyear
        else: limits[i] = limits[i] # This leaves limits[i] untouched if it's a number or something
    
    # Wrap up
    if isstring: return limits[0] # Return just a scalar
    if istuple: return tuple(limits) # Convert back to a tuple
    else: return limits # Or return the whole list