"""
This module defines the Results class, which stores the results of a single simulation run.

Version: 2015nov02 by cliffk
"""

from optima import uuid, today, quantile, printv, odict
from numpy import array, transpose


class Result(object):
    ''' A tiny class just to hold overall and by-population results '''
    def __init__(self, name=None, isnumber=True, pops=None, tot=None):
        self.pops = pops
        self.tot = tot
        self.name = name
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
        self.main['prev'] = Result('HIV prevalence', isnumber=False)
        self.main['force'] = Result('Force-of-infection', isnumber=False)
        self.main['numinci'] = Result('Number of new infections')
        self.main['numplhiv'] = Result('Number of PLHIV')
        self.main['dalys'] = Result('Number of DALYs')
        self.main['numdeath'] = Result('Number of HIV-related deaths')
        self.main['numtreat'] = Result('Number of people on treatment')
        self.main['numdiag'] = Result('Number of people diagnosed')
        self.main['numnewtreat'] = Result('Number of people newly treated')
        self.main['numnewdiag'] = Result('Number of new diagnoses')
        
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
        
    

    
    
    def makeplots(self, whichplots=None, uncertainty=False, verbose=2, figsize=(8,6)):
        ''' Render the plots requested and store them in a list '''
        from pylab import isinteractive, ioff, ion, figure, plot, xlabel, ylabel, close, xlim, ylim
        wasinteractive = isinteractive() # Get current state of interactivity
        ioff() # Just in case, so we don't flood the user's screen with figures
        if type(whichplots)==str: whichplots = [whichplots] # Convert to list
        plots = odict()
        for pl in whichplots:
            try:
                datatype, poptype = pl.split('-')
                if datatype not in self.main.keys(): 
                    errormsg = 'Could not understand plot "%s"; ensure keys are one of:\n' % datatype
                    errormsg += '%s' % self.main.keys()
                    raise Exception(errormsg)
                if poptype not in ['pops', 'tot']: 
                    errormsg = 'Type "%s" should be either "pops" or "tot"'
                    raise Exception(errormsg)
            except:
                errormsg = 'Could not parse plot "%s"\n' % pl
                errormsg += 'Please ensure format is e.g. "numplhiv-tot"'
                raise Exception(errormsg)
            if not uncertainty: thisdata = getattr(self.main[datatype], poptype)[0] # Either 'tot' or 'pops'
            else: raise Exception('WARNING, uncertainty in plots not implemented yet')
            plots[pl] = figure(figsize=figsize)
            plot(self.tvec, transpose(array(thisdata))) # Actually do the plot
            xlabel('Year')
            ylabel(self.main[datatype].name)
            currentylims = ylim()
            ylim((0,currentylims[1]))
            xlim((self.tvec[0], self.tvec[-1]))
            close(plots[pl])
        
        if wasinteractive: ion() # Turn interactivity back on
        return plots