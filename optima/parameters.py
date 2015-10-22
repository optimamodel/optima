# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 15:22:00 2015

@author: cliffk
"""

from uuid import uuid4
from datetime import datetime

class Parameterset(object):
    ''' A full set of all parameters '''
    
    def __init__(self, name='default'):
        self.name = name
        self.id = uuid4()
        self.created = datetime.today()
        self.modified = datetime.today()
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += 'Parameter set name: %s\n'    % self.name
        output += '      Date created: %s\n'    % self.getdate(which='created')
        output += '     Date modified: %s\n'    % self.getdate(which='modified')
        output += '                ID: %s\n'    % self.id
        return output
    
    def makeparset(self):
        
    
    
    
    
    
    
    
    
    def listpars():
        ''' A method for listing all parameters '''
    
    def plotpars():
        ''' Plot all parameters, I guess against data '''


class Parameter(object):
    ''' The definition of a single parameter '''
    
    def __init__(self):
        self.full = None
        self.short = None
        self.t = None
        self.y = None
        self.m = None
        