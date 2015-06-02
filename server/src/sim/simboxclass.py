# -*- coding: utf-8 -*-
"""
Created on Tue Jun 02 01:03:34 2015

@author: David Kedziora
"""

class SimBox:
    def __init__(self, simboxname):
        self.simboxname = simboxname
        
        self.simlist = []
        
    def setsimboxname(self, simboxname):
        self.simboxname = simboxname
        
    def getsimboxname(self):
        return self.simboxname
        
class Sim:
    def __init__(self, simname):
        self.simname = simname
        
    def setsimname(self, simname):
        self.simname = simname
        
    def getsimname(self):
        return self.simname