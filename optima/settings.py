"""
SETTINGS

Store all the static data for a project that won't change except between Optima versions.

Version: 2016jan06 by cliffk
"""

from numpy import arange, array, concatenate as cat, linspace
from optima import defaultrepr


class Settings():
    def __init__(self):
        self.dt = 0.2 # Timestep
        self.start = 2000.0 # Default start year
        self.end = 2030.0 # Default end year
        self.hivstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'lt50']
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
        self.sus      = cat([self.uncirc, self.circ]) # All uninfected
        self.alldx    = cat([self.dx, self.care, self.usvl, self.svl, self.lost, self.off]) # All people diagnosed
        self.allplhiv = cat([self.undx, self.alldx]) # All PLHIV
        self.alltreat = cat([self.usvl, self.svl]) # All PLHIV
        self.allstates = cat([self.sus, self.allplhiv]) # All states
        self.nstates = len(self.allstates) # Total number of states

		# Non-cascade settings/states
		self.usecascade = True # Whether or not to actually use the cascade
		self.tx  = self.svl # Infected, on treatment -- not used with the cascade
		self.noncascadestates = cat([self.uncirc, self.circ, self.undx, self.dx, self.tx]) # Specify the non-cascade states -- WARNING, not sure if will be used
        
        # Other
        self.optimablue = (0.16, 0.67, 0.94) # The color of Optima
        self.verbose = 2 # Default verbosity for how much to print out
    
    
    def __repr__(self):
        ''' Prettily print object '''
        output =  defaultrepr(self)
        return output
    
    
    def maketvec(self, start=None, end=None, dt=None):
        ''' Little function for calculating the time vector -- here since start, end, dt are stored here '''
        if start is None: start=self.start
        if end is None: end=self.end
        if dt is None: dt=self.dt
        tvec = linspace(start, end, round((end-start)/dt)+1)
        return tvec


    def setmaxes(self, maxlist=None, dt=None):
        ''' Method to calculate maximum limits '''
        if dt is None: dt = self.dt
        maxrate = 0.9/dt
        maxpopsize = 1e9
        maxmeta = 1000.0
        maxacts = 5000.0
        
        # Just return the limits themselves if no input argument
        if maxlist is None: 
            return (maxrate, maxpopsize, maxmeta, maxacts)
        
        # If list argument is given, replace text labels with numeric limits
        else:
            for i,m in enumerate(maxlist):
                if m=='maxrate': maxlist[i] = maxrate
                elif m=='maxpopsize': maxlist[i] = maxpopsize
                elif m=='maxmeta': maxlist[i] = maxmeta
                elif m=='maxacts': maxlist[i] = maxacts
                else: pass
            return maxlist
