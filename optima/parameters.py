"""
This module defines the Parameter and Parameterset classes, which are 
used to define a single parameter (e.g., hivtest) and the full set of
parameters, respetively.

Version: 2015oct22 by cliffk
"""


from numpy import array, isnan, zeros, shape, mean
from utils import printv, sanitize, save, uuid, today, getdate



class Parameter(object):
    ''' The definition of a single parameter '''
    
    def __init__(self, name='', t=[], y=[], m=1):
        self.name = name# Parameter name
        self.t = t # Time data, e.g. [2002, 2008]
        self.y = y # Value data, e.g. [0.3, 0.7]
        self.m = m # Multiplicative metaparameter, e.g. 1
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += 'Parameter name: %s\n'    % self.name
        output += '   Time points: %s\n'    % self.t
        output += '        Values: %s\n'    % self.y
        output += ' Metaparameter: %s\n'    % self.m
        return output





class Parameterset(object):
    ''' A full set of all parameters, possibly including multiple uncertainty runs '''
    
    def __init__(self, name='default'):
        self.name = name # Name of the parameter set, e.g. 'default'
        self.id = uuid() # ID
        self.created = today() # Date created
        self.modified = today() # Date modified
        self.pars = [] # List of Parameters objects -- only one if no uncertainty
    
    def __repr__(self):
        ''' Print out useful information when called'''
        output = '\n'
        output += 'Parameter set name: %s\n'    % self.name
        output += '    Number of runs: %s\n'    % len(self.pars)
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '                ID: %s\n'    % self.id
        return output
    
    
    def save(self, filename=None): # WARNING, can we just use a generic save method? Do we really need a different one for each object?
        ''' Save this parameter set to a file '''
        if filename is None: filename = self.name+'.pars'
        save(self, filename)
        return None
    
    
    def listpars():
        ''' A method for listing all parameters '''
    
    
    def plotpars():
        ''' Plot all parameters, I guess against data '''


    def makeparsfromdata(self, data, verbose=2):
        """
        Translates the raw data (which were read from the spreadsheet). into
        parameters that can be used in the model. These data are then used to update 
        the corresponding model (project). This method should be called before a 
        simulation is run.
        
        Version: 2015oct22 by cliffk
        """
        
        printv('Converting data to parameters...', 1, verbose)
        
        
        def data2par(parname, dataarray, usetime=True):
            """ Take an array of data and turn it into default parameters -- here, just take the means """
            nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
            par = Parameter() # Create structure
            par.name = parname # Store the name of the parameter
            par.m = 1 # Set metaparameter to 1
            par.y = [0]*nrows # Initialize array for holding population parameters
            if usetime:
                par.t = [0]*nrows # Initialize array for holding time parameters
                for r in range(nrows): 
                    validdata = ~isnan(dataarray[r])
                    if sum(validdata): # There's at least one data point
                        par.y[r] = sanitize(dataarray[r]) # Store each extant value
                        par.t[r] = array(data['years'])[~isnan(dataarray[r])] # Store each year
                    else: # Blank, assume zero
                        par.y[r] = array([0])
                        par.t[r] = array([0])
        
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
        def popexpand(origpar, popbool):
            """ For variables that are only defined for certain populations, expand to the full array. WARNING, doesn't work for time """
            newpar = Parameter()
            newpar.y = [array([0]) for i in range(len(data['pops']['male']))]
            newpar.t = [array([0]) for i in range(len(data['pops']['male']))]
            count = -1
            if hasattr(popbool,'__iter__'): # May or may not be a list
                for i,tf in enumerate(popbool):
                    if tf:
                        count += 1
                        newpar.y[i] = origpar.y[count]
                        newpar.t[i] = origpar.t[count]
            
            return newpar
        
        
        
        
        
        
        
        ###############################################################################
        ## Loop over quantities
        ###############################################################################
        
        pars = dict()
        
        ## Key parameters
        for parname in ['popsize', 'hivprev']:
            pars[parname] = dataindex(data[parname][0], 0) # WARNING, will want to change
        
        ## Parameters that can be converted automatically
        sheets = data['meta']['sheets']
        
        for parname in sheets['Other epidemiology'] + sheets['Testing & treatment'] + sheets['Sexual behavior'] + sheets['Injecting behavior']:
            printv('Converting data parameter %s...' % parname, 3, verbose)
            pars[parname] = data2par(parname, data[parname])
        

        # Fix up ones of the wrong size
        pars['birth']     = popexpand(pars['birth'],     array(data['pops']['female'])==1)
        pars['circum']    = popexpand(pars['circum'],    array(data['pops']['male'])==1)
        
        
        ## WARNING, not sure what to do with these
        for parname in ['partreg', 'partcas', 'partcom', 'partinj', 'transsym', 'transasym']:
            printv('Converting data parameter %s...' % parname, 3, verbose)
            pars[parname] = data[parname]
        
        pars['const'] = dict()
        for parname in data['const'].keys():
            printv('Converting data parameter %s...' % parname, 3, verbose)
            pars['const'][parname] = data['const'][parname][0] # Taking best value only, hence the 0

        
        self.pars.append(pars)
        
        printv('...done converting data to parameters.', 2, verbose)
        
        return None