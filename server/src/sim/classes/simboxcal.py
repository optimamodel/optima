# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 23:52:18 2015

@author: David Kedziora
"""

from simbox import SimBox

# A container for calibrating Sims.
class SimBoxCal(SimBox):
    def __init__(self,name,region):
        SimBox.__init__(self,name,region)
        
    def load_dict(self, simboxdict):
        SimBox.load_dict(self,simboxdict)
       
    def todict(self):
        simboxdict = SimBox.todict(self)
        simboxdict['type'] = 'SimBoxCal'    # Overwrites SimBox type.
        
        return simboxdict

    def __repr__(self):
        return "SimBoxCal %s ('%s')" % (self.uuid[0:8],self.name)