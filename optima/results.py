"""
This module defines the Results class, which stores the results of a single simulation run.

Version: 2015nov02 by cliffk
"""

from optima import uuid, today, quantile, printv
from numpy import array


class Result(object):
    ''' A tiny class just to hold overall and by-population results '''
    def __init__(self, isnumber=True):
        self.pops = None
        self.tot = None
        self.isnumber = isnumber
        


class Results(object):
    ''' Lightweight structure to hold results -- use this instead of a dict '''
    def __init__(self):
        # Basic info
        self.uuid = uuid()
        self.created = today()
        self.projectinfo = None
        self.pars = None
        
        # Fundamental quantities
        self.tvec = None
        self.people = None
        
        # Main results -- time series, by population
        self.main = odict() # For storing main results
        self.main['prev'] = Result(isnumber=False)
        self.main['force'] = Result(isnumber=False)
        self.main['numinci'] = Result()
        self.main['numplhiv'] = Result()
        self.main['dalys'] = Result()
        self.main['numdeath'] = Result()
        self.main['numtreat'] = Result()
        self.main['numdiag'] = Result()
        self.main['numnewtreat'] = Result()
        self.main['numnewdiag'] = Result()
        
        # Other quantities
        self.births = Result()
        self.mtct = Result()
        self.newtreat = Result()
        self.newcircum = Result()
        self.numcircum = Result()
        self.reqcircum = Result()
        self.sexinci = Result()
    
#    def __repr__(self):
#        ''' This will eventually include information that's useful... '''
    
    
#    def plot():
    
    
    
    def derivedresults(self, verbose=2):
        """ Gather standard results into a form suitable for plotting with uncertainties. """
        
        printv('Making derived results...', 3, verbose)
        
        if self.people is None:
            raise Exception('It seems the model has not been run yet, people is empty!')
        
        ## WARNING, TEMP
        quantiles = [0.5]
        allpeople = array([self.people]) 
        
        self.main['prev'].pops = quantile(allpeople[:,1:,:,:].sum(axis=1) / allpeople[:,:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['prev'].tot = quantile(allpeople[:,1:,:,:].sum(axis=(1,2)) / allpeople[:,:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        
        self.main['numplhiv'].pops = quantile(allpeople[:,1:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['numplhiv'].tot = quantile(allpeople[:,1:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
        
        allinci = array([self.inci])
        self.main['numinci'].pops = quantile(allinci, quantiles=quantiles)
        self.main['numinci'].tot = quantile(allinci.sum(axis=1), quantiles=quantiles) # Axis 1 is populations


        allinci = array([self.inci])
        self.main['force'].pops = quantile(allinci / allpeople[:,:,:,:].sum(axis=1), quantiles=quantiles) # Axis 1 is health state
        self.main['force'].tot = quantile(allinci.sum(axis=1) / allpeople[:,:,:,:].sum(axis=(1,2)), quantiles=quantiles) # Axis 2 is populations
    
    
        alldeaths = array([self.death])
        self.main['numdeath'].pops = quantile(alldeaths, quantiles=quantiles)
        self.main['numdeath'].tot = quantile(alldeaths.sum(axis=1), quantiles=quantiles) # Axis 1 is populations

        alldx = array([self.dx])
        self.main['numdiag'].pops = quantile(alldx, quantiles=quantiles)
        self.main['numdiag'].tot = quantile(alldx.sum(axis=1), quantiles=quantiles) # Axis 1 is populations

# WARNING, need to implement
#        disutils = [D[self.pars['const']['disutil'][key] for key in D['G['healthstates']]
#        tmpdalypops = allpeople[:,concatenate([D['G['tx1'], D['G['tx2']]),:,:].sum(axis=1) * D['P['const['disutil['tx']
#        tmpdalytot = allpeople[:,concatenate([D['G['tx1'], D['G['tx2']]),:,:].sum(axis=(1,2)) * D['P['const['disutil['tx']
#        for h in xrange(len(disutils)): # Loop over health states
#            healthstates = array([D['G['undx'][h], D['G['dx'][h], D['G['fail'][h]])
#            tmpdalypops += allpeople[:,healthstates,:,:].sum(axis=1) * disutils[h]
#            tmpdalytot += allpeople[:,healthstates,:,:].sum(axis=(1,2)) * disutils[h]
#        self.daly.pops = quantile(tmpdalypops, quantiles=quantiles)
#        self.daly.tot = quantile(tmpdalytot, quantiles=quantiles)
        
    

    
    
    def makeplots(self, whichplots=None, verbose=2):
        ''' Reder the plots requested and store them in a list '''
        ioff() # Just in case, so we don't flood the user's screen with
        if type(whichplots)==str: whichplots = [whichplots] # Convert to list
        plots = odict()
        for pl in whichplots:
            thisdata
            thisdata = getattr(whichplots[j],this[0]),this[1])[0]
            axes[-1].plot(self.resultslist[j].tvec, transpose(array(thisdata)), linestyle=self.resultslist[0].styles[j])

        return plots