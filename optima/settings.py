"""
SETTINGS

Store all the static data for a project that won't change except between Optima versions.

Version: 2015nov22 by cliffk
"""

from numpy import arange

class Settings():
    def __init__(self):
        self.dt = 0.2 # Timestep
        self.hivstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
        self.ncd4 = len(self.hivstates)
        self.uninf  = arange(0,1) # Uninfected
        self.undiag = arange(0*self.ncd4+1, 1*self.ncd4+1) # Infected, undiagnosed
        self.diag   = arange(1*self.ncd4+1, 2*self.ncd4+1) # Infected, diagnosed
        self.treat  = arange(2*self.ncd4+1, 3*self.ncd4+1) # Infected, on treatment
        self.ncomparts = self.treat[-1]+1 # +1 because of indexing
        