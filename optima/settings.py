"""
SETTINGS

Store all the static data for a project that won't change except between Optima versions.

Version: 2015nov22 by cliffk
"""

from numpy import arange, concatenate as cat

class Settings():
    def __init__(self):
        self.dt = 0.2 # Timestep
        self.start = 2000 # Default start year
        self.end = 2030 # Default end year
        self.hivstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
        self.ncd4 = len(self.hivstates)
        
        # Original states
        self.uncirc = arange(0,1) # Uninfected, uncircumcised
        self.circ   = arange(1,2) # Uninfected, circumcised
        self.undiag = arange(0*self.ncd4+2, 1*self.ncd4+2) # Infected, undiagnosed
        self.diag   = arange(1*self.ncd4+2, 2*self.ncd4+2) # Infected, diagnosed
        self.treat  = arange(2*self.ncd4+2, 3*self.ncd4+2) # Infected, on treatment
        
        # Combined states
        self.alluninf = cat([self.uncirc, self.circ]) # All uninfected
        self.alldiag = cat([self.diag, self.treat]) # All people diagnosed
        self.allplhiv = cat([self.undiag, self.alldiag]) # All PLHIV
        self.allstates = cat([self.alluninf, self.allplhiv]) # All states
        self.ncomparts = len(self.allstates) # Total number of states
        