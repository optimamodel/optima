"""
Test to see if the calculation of people has changed.

Version: 2016feb06
"""

from numpy import shape
import optima as op
import os


refresh = 0 # Creates defaultpeople.ppl rather than copares
eps = 1e-3 # Don't expect a totally exact match
filename = 'defaultpeople.npy'

P = op.defaults.defaultproject('generalized')
newpeople = P.results[0].raw[0]['people']

if refresh or not(os.path.exists(filename)):
    op.saveobj(filename, newpeople)
    print('Created new "%s".' % filename)
else:
    oldpeople = op.loadobj(filename)
    diffpeople = newpeople-oldpeople
    
    if (diffpeople>eps).any(): # If not every element is a real number >0, throw an error
        for t in range(shape(diffpeople)[2]): # Loop over all heath states
            for errstate in range(shape(diffpeople)[0]): # Loop over all heath states
                for errpop in range(shape(diffpeople)[1]): # Loop over all populations
                    if diffpeople[errstate,errpop,t]!=0:
                        errormsg = 'WARNING, people do not match!\npeople[%i, %i, %i] = %f vs. %f' % (errstate, errpop, t, oldpeople[errstate,errpop,t], newpeople[errstate,errpop,t])
                        raise Exception(errormsg)
    else:
        print('People are the same, yay! (max diff: %s)' % diffpeople.max())