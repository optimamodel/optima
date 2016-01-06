"""
SETTINGS

Store all the static data for a project that won't change except between Optima versions.

Version: 2015nov22 by cliffk
"""

from numpy import arange, array, concatenate as cat


class Settings():
    def __init__(self):
        self.dt = 0.2 # Timestep
        self.start = 2000.0 # Default start year
        self.end = 2030.0 # Default end year
        self.hivstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
        self.ncd4 = len(self.hivstates)
        
        # Original states by diagnosis
        self.uncirc = arange(0,1) # Uninfected, uncircumcised
        self.circ   = arange(1,2) # Uninfected, circumcised
        self.undiag = arange(0*self.ncd4+2, 1*self.ncd4+2) # Infected, undiagnosed
        self.diag   = arange(1*self.ncd4+2, 2*self.ncd4+2) # Infected, diagnosed
        self.treat  = arange(2*self.ncd4+2, 3*self.ncd4+2) # Infected, on treatment
        
        # Original states by CD4 count
        self.acute = array([2,8,14]) 
        self.gt500 = array([3,9,15]) 
        self.gt350 = array([4,10,16]) 
        self.gt200 = array([5,11,17]) 
        self.gt50  = array([6,12,18]) 
        self.aids  = array([7,13,19]) 

        # Combined states
        self.alluninf = cat([self.uncirc, self.circ]) # All uninfected
        self.alldiag = cat([self.diag, self.treat]) # All people diagnosed
        self.allplhiv = cat([self.undiag, self.alldiag]) # All PLHIV
        self.allstates = cat([self.alluninf, self.allplhiv]) # All states

        self.nstates = len(self.allstates) # Total number of states
        
        # Other
        self.optimablue = (0.16, 0.67, 0.94) # The color of Optima
    
    def __repr__(self):
        output =  '                  Optima settings\n'
        output += '============================================================\n'
        for key in self.__dict__.keys():
            output += ' %10s: %s\n' % (key, str(getattr(self, key)))
        output += '============================================================\n'
        return output


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
