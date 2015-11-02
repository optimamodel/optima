"""
This module defines the Results class, which stores the results of a single simulation run.

Version: 2015nov02 by cliffk
"""

from utils import uuid, today
from numpy import zeros, nan, size, ndim, array, asarray
from printv import printv
from copy import deepcopy

class Results(object):
    ''' Lightweight structure to hold results -- use this instead of a dict '''
    def __init__(self):
        # Basic info
        self.id = uuid()
        self.created = today()
        self.projectinfo = None
        self.pars = None
        
        # Fundamental quantities
        self.tvec = None
        self.people = None
        
        # Key results
        self.prev = None
        self.inci = None
        self.plhiv = None
        self.dalys = None
        self.death = None
        self.treat = None
        
        # Other quantities
        self.births = None
        self.dx = None
        
        self.mtct = None
        self.newtx = None
        self.newcircum = None
        self.numcircum = None
        self.reqcircum = None
        self.sexinci = None
        
    
    
    
    def derivedresults(self, verbose=2):
        """ Gather standard results into a form suitable for plotting with uncertainties. """
        
        printv('Making derived results...', 3, verbose)
        
        if self.people is None:
            raise Exception('It seems the model has not been run yet!')
        
        