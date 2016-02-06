"""
Test to see if the calculation of people has changed.

Version: 2016feb06
"""

from numpy import shape
import optima as op
import os


refresh = False # Creates defaultpeople.ppl rather than copares
P = op.defaults.defaultproject('generalized')
filename = 'defaultpeople.ppl'

newpeople = P.results[0].raw[0]['people']

if refresh or not(os.path.exists(filename)):
    op.saveobj(filename, newpeople)
    print('Created new "%s".' % filename)
else:
    oldpeople = op.loadobj(filename)
    diffpeople = newpeople-oldpeople
    
    if (diffpeople!=0).any(): # If not every element is a real number >0, throw an error
        for t in range(shape(diffpeople)[2]): # Loop over all heath states
            for errstate in range(shape(diffpeople)[0]): # Loop over all heath states
                for errpop in range(shape(diffpeople)[1]): # Loop over all populations
                    if diffpeople[errstate,errpop,t]!=0:
                        errormsg = 'WARNING, People do not match!\npeople[%i, %i, %i] = %f vs. %f' % (errstate, errpop, t, oldpeople[errstate,errpop,t], newpeople[errstate,errpop,t])
                        raise Exception(errormsg)
    else:
        print('People are the same, yay!')