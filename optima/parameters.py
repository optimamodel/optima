"""
This module defines the Parameter and Parameterset classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, respetively.

Version: 2015oct22 by cliffk
"""

from uuid import uuid4
from datetime import datetime
from utils import printv
from numpy import array as ar, isnan, zeros, shape, mean
from utils import sanitize
try: import cPickle as pickle # For Python 2 compatibility
except: import pickle
from gzip import GzipFile



class Parameter(object):
    ''' The definition of a single parameter '''
    
    def __init__(self, full=None, short=None, t=[], y=[], m=1):
        self.full = full # Full parameter name
        self.short = short # Short parameter name
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]
        self.m = m # Multiplicative metaparameter, e.g. 1





class Parameters(object):
    ''' A complete set of parameters required for a simulation run '''






class Parameterset(object):
    ''' A full set of all parameters, possibly including multiple uncertainty runs '''
    
    def __init__(self, name='default'):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.id = uuid4() # ID
        self.created = datetime.today() # Date created
        self.modified = datetime.today() # Date modified
        self.pars = [] # List of Parameters objects -- only one if no uncertainty
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += 'Parameter set name: %s\n'    % self.name
        output += '    Number of runs: %s\n'    % len(self.pars)
        output += '      Date created: %s\n'    % self.getdate(which='created')
        output += '     Date modified: %s\n'    % self.getdate(which='modified')
        output += '                ID: %s\n'    % self.id
        return output
    
    
    def save(self, filename=None): # WARNING, can we just use a generic save method? Do we really need a different one for each object?
        ''' Save this parameter set to a file '''
        if filename is None: filename = self.name+'.pars'
        with GzipFile(filename, 'wb') as fileobj: pickle.dump(self, fileobj, protocol=2)
        print('Parameter set "%s" saved to "%s"' % (self.name, filename))
        return None
    
    
    def listpars():
        ''' A method for listing all parameters '''
    
    
    def plotpars():
        ''' Plot all parameters, I guess against data '''


    def data2pars(self, data, verbose=2):
        """
        Translates the raw data (which were read from the spreadsheet). into
        parameters that can be used in the model. These data are then used to update 
        the corresponding model (project). This method should be called before a 
        simulation is run.
        
        Version: 2015oct22 by cliffk
        """
        
        printv('Converting data to parameters...', 1, verbose)
        
        
        def data2par(dataarray, usetime=True):
            """ Take an array of data and turn it into default parameters -- here, just take the means """
            nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
            par = Parameter() # Create structure
            par.m = 1 # Set metaparameter to 1
            par.y = [0]*nrows # Initialize array for holding population parameters
            if usetime:
                par.t = [0]*nrows # Initialize array for holding time parameters
                for r in range(nrows): 
                    validdata = ~isnan(dataarray[r])
                    if sum(validdata): # There's at least one data point
                        par.y[r] = sanitize(dataarray[r]) # Store each extant value
                        par.t[r] = ar(data['epiyears'])[~isnan(dataarray[r])] # Store each year
                    else: # Blank, assume zero
                        par.y[r] = ar([0])
                        par.t[r] = ar([0])
        
            else:
                raise Exception('Not implemented')
                for r in range(nrows): 
                    par['p'][r] = mean(sanitize(dataarray[r])) # Calculate mean for each population
                    print('TMP223')
            
            return par
        
        
        
        def dataindex(dataarray, index):
            """ Take an array of data return either the first or last (...or some other) non-NaN entry """
            nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
            output = zeros(nrows) # Create structure
            for r in range(nrows): 
                output[r] = sanitize(dataarray[r])[index] # Return the specified index -- usually either the first [0] or last [-1]
            
            return output
        
        
        
        
        ## Change sizes of circumcision and births
        def popexpand(origarray, popbool):
            """ For variables that are only defined for certain populations, expand to the full array. WARNING, doesn't work for time """
            from copy import deepcopy
            newarray = deepcopy(origarray)
            if 't' in newarray.keys(): 
                newarray['p'] = [ar([0]) for i in range(len(data['popprog']['pops']['male']))]
                newarray['t'] = [ar([0]) for i in range(len(data['popprog']['pops']['male']))]
                count = -1
                if hasattr(popbool,'__iter__'): # May or may not be a list
                    for i,tf in enumerate(popbool):
                        if tf:
                            count += 1
                            newarray['p'][i] = origarray['p'][count]
                            newarray['t'][i] = origarray['t'][count]
            else: 
                newarray['p'] = zeros(shape(data['popprog']['pops']['male']))
                count = -1
                if hasattr(popbool,'__iter__'): # May or may not be a list
                    for i,tf in enumerate(popbool):
                        if tf:
                            count += 1
                            newarray['p'][i] = origarray['p'][count]
            
            return newarray
        
        
        
        
        
        
        
        ###############################################################################
        ## Loop over quantities
        ###############################################################################
        
        ## Key parameters
        self.popsize = dataindex(data['popsize'][0], 0) # WARNING, will want to change
        self.hivprev = dataindex(data['hivprev'][0], 0) # WARNING, will want to change
        
        ## Parameters that can be converted automatically
        self.death      = data2par(data['epi']['death'])
        self.tbprev     = data2par(data['epi']['tbprev'])
        self.stiprevdis = data2par(data['epi']['stiprevdis'])
        self.stiprevulc = data2par(data['epi']['stiprevulc'])
        
        self.numtx    = data2par(data['txrx']['numtx'])
        self.numpmtct = data2par(data['txrx']['numpmtct'])
        self.txelig   = data2par(data['txrx']['txelig'])
        self.breast   = data2par(data['txrx']['breast'])
        self.birth    = data2par(data['txrx']['birth'])
        self.hivtest  = data2par(data['txrx']['hivtest'])
        self.aidstest = data2par(data['txrx']['aidstest'])
        self.prep     = data2par(data['txrx']['prep'])
        
        self.numactsreg = data2par(data['sex']['numactsreg'])
        self.numactscas = data2par(data['sex']['numactscas'])
        self.numactscom = data2par(data['sex']['numactscom'])
        self.condomreg  = data2par(data['sex']['condomreg'])
        self.condomcas  = data2par(data['sex']['condomcas'])
        self.condomcas  = data2par(data['sex']['condomcas'])
        self.circum     = data2par(data['sex']['circum'])
        
        self.numinject = data2par(data['inj']['numinject'])
        self.sharing   = data2par(data['inj']['sharing'])
        self.numost    = data2par(data['inj']['numost'])
        
        # Fix up ones of the wrong size
        self.birth      = popexpand(self.birth,     ar(data['popprog']['pops']['female'])==1)
        self.circum    = popexpand(self.circum,    ar(data['popprog']['pops']['male'])==1)
        
        
        ## WARNING, not sure what to do with these
        self.pships = data['pships'] 
        self.transit = data['transit']
        
        self.const = dict()
        for parclass in data['const'].keys():
            printv('Converting data parameter %s...' % parclass, 3, verbose)
            if type(data['const'][parclass])==dict: 
                self.const[parclass] = dict()
                for parname in data['const'][parclass].keys():
                    printv('Converting data parameter %s...' % parname, 4, verbose)
                    self.const[parclass][parname] = data['const'][parclass][parname][0] # Taking best value only, hence the 0

        
        
        printv('...done converting data to parameters.', 2, verbose)