"""
SETTINGS

Store all the static data for a project that won't change except between Optima versions.

Version: 2015sep02
"""

from numpy import arange

hivstates = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
ncd4 = len(hivstates)
uninf  = arange(0,1) # Uninfected
undiag = arange(0*ncd4+1, 1*ncd4+1) # Infected, undiagnosed
diag   = arange(1*ncd4+1, 2*ncd4+1) # Infected, diagnosed
treat  = arange(2*ncd4+1, 3*ncd4+1) # Infected, on treatment
fail   = arange(3*ncd4+1, 4*ncd4+1) # Infected, treatment failure
ncomparts = fail[-1]+1 # +2 because of indexing