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
        self.diag = None
        
        # Other quantities
        self.births = None
        self.mtct = None
        self.newtreat = None
        self.newcircum = None
        self.numcircum = None
        self.reqcircum = None
        self.sexinci = None
        
    
    
    
    def derivedresults(self, verbose=2):
        """ Gather standard results into a form suitable for plotting with uncertainties. """
        
        printv('Making derived results...', 3, verbose)
        
        if self.people is None:
            raise Exception('It seems the model has not been run yet, people is empty!')
        
        self.prev['pops'] = quantile(allpeople[:,1:,:,:].sum(axis=1) / allpeople[:,:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.prev['tot'] = quantile(allpeople[:,1:,:,:].sum(axis=(1,2)) / allpeople[:,:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        
        self.plhiv['pops'] = quantile(allpeople[:,1:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.plhiv['tot'] = quantile(allpeople[:,1:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        
        allinci = array([allsims[s]['inci'] for s in xrange(nsims)])
        self.inci['pops'] = quantile(allinci, quantiles=quantiles)
        self.inci['tot'] = quantile(allinci.sum(axis=1), quantiles=quantiles) # Axis 1 is populations


        allinci = array([allsims[s]['inci'] for s in xrange(nsims)])
        self.force['pops'] = quantile(allinci / allpeople[:,:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.force['tot'] = quantile(allinci.sum(axis=1) / allpeople[:,:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
    
    
        alldeaths = array([allsims[s]['death'] for s in xrange(nsims)])
        self.death['pops'] = quantile(alldeaths, quantiles=quantiles)
        self.death['tot'] = quantile(alldeaths.sum(axis=1), quantiles=quantiles) # Axis 1 is populations

        disutils = [D['P['const['disutil'][key] for key in D['G['healthstates']]
        tmpdalypops = allpeople[:,concatenate([D['G['tx1'], D['G['tx2']]),:,:].sum(axis=1) * D['P['const['disutil['tx']
        tmpdalytot = allpeople[:,concatenate([D['G['tx1'], D['G['tx2']]),:,:].sum(axis=(1,2)) * D['P['const['disutil['tx']
        for h in xrange(len(disutils)): # Loop over health states
            healthstates = array([D['G['undx'][h], D['G['dx'][h], D['G['fail'][h]])
            tmpdalypops += allpeople[:,healthstates,:,:].sum(axis=1) * disutils[h]
            tmpdalytot += allpeople[:,healthstates,:,:].sum(axis=(1,2)) * disutils[h]
        self.daly['pops'] = quantile(tmpdalypops, quantiles=quantiles)
        self.daly['tot'] = quantile(tmpdalytot, quantiles=quantiles)
        
    
        alldx = array([allsims[s]['dx'] for s in xrange(nsims)])
        self.dx['pops'] = quantile(alldx, quantiles=quantiles)
        self.dx['tot'] = quantile(alldx.sum(axis=1), quantiles=quantiles) # Axis 1 is populations