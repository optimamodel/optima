# -*- coding: utf-8 -*-
"""
Created on Fri May 29 23:16:12 2015

@author: David Kedziora
"""

import defaults
from simbox import SimBox, SimBoxOpt
import sim
import setoptions
import uuid
import program

from scipy.interpolate import PchipInterpolator as pchip

#### Multiprocessor helper functions for Region class.
#def unwrap_self_developBOCsubprocess(*arg, **kwarg):
#    return Region.developBOCsubprocess(*arg, **kwarg)
#    
#def f(x):
#    return x**2

### The actual Region class.
class Region:
    def __init__(self, name,populations,programs,datastart,dataend):
        # The standard constructor takes in the initial metadata directly
        # In normal usage, this information would come from the frontend
        # whether web interface, or an interactive prompt

        self.D = dict()                 # Data structure for saving everything. Will hopefully be broken down eventually.
              
        self.metadata = defaults.metadata  # Loosely analogous to D['G']. Start with default HIV metadata
        self.metadata['datastart'] = datastart
        self.metadata['dataend'] = dataend
        self.metadata['populations'] = populations
        self.metadata['programs'] = programs
        self.metadata['name'] = name

        self.data = None

        self.options = setoptions.setoptions() # Populate default options here
        
        # Budget Objective Curve data, used for GPA. (Assuming initial budget spending is fixed.)
        self.BOCx = []        # Array of budget allocation totals.
        self.BOCy = []        # Array of corresponding optimum objective values.
        
        self.program_sets = []
        self.calibrations = []        # Remember. Current BOC data assumes loaded data is calibrated by default.
        
        self.simboxlist = []            # Container for simbox objects (e.g. optimisations, grouped scenarios, etc.)
    
        self.uuid = str(uuid.uuid4()) # Store UUID as a string - we just want a (practically) unique tag, no advanced functionality


    @classmethod
    def load(Region,filename,name=None):
        # Create a new region by loading a JSON file
        # If a name is not specified, the one contained in the JSON file is used
        # Note that this function can be used with an old-type or new-type JSON file
        # A new-type JSON file will read a Region object including the UUID
        # While an old-type JSON file corresponds to 'D' and the region will get a new UUID
        r = Region(name,None,None,None,None)

        import dataio
        regiondict = dataio.loaddata(filename)
        if 'uuid' in regiondict.keys(): # This is a new-type JSON file
            print "This is a new-type JSON file."
            r.uuid = regiondict['uuid'] # Loading a region restores the original UUID
            r.fromdict(regiondict)
        else:
            r.fromdict_legacy(regiondict)
        return r

    def fromdict(self,regiondict):
        # Assign variables from a new-type JSON file created using Region.todict()
        self.metadata = regiondict['metadata']
        self.data = regiondict['data']
        self.options = regiondict['options'] # Populate default options here
        self.program_sets = regiondict['program_sets'] # sets of Programs i.e. an array of sets of CCOCs
        
        import numpy
        if isinstance(regiondict['calibrations'], float) and numpy.isnan(regiondict['calibrations']):
            regiondict['calibrations'] = [{'uuid':None}]
        self.calibrations = regiondict['calibrations']
        self.uuid = regiondict['uuid']
        self.D = regiondict['D']
        
        self.simboxlist = []
        for x in regiondict['simboxlist']:
            if x['type'] == 'SimBoxOpt':
                self.simboxlist.append(SimBoxOpt.fromdict(x,self))
            else:
                self.simboxlist.append(SimBox.fromdict(x,self))

        # BOC loading.
        self.BOCx = regiondict['BOC_budgets']
        self.BOCy = regiondict['BOC_objectives']
            
    def fromdict_legacy(self, tempD):
        # Load an old-type D dictionary into the region

        self.setD(tempD)                # It would be great to get rid of setD one day. But only when data is fully decomposed.
        
        current_name = self.metadata['name']
        self.metadata = tempD['G'] # Copy everything from G by default
        self.metadata['programs'] = tempD['programs']
        self.metadata['populations'] = self.metadata['inputpopulations']
        if current_name is not None: # current_name is none if this function is being called from Region.load()
            self.metadata['name'] = current_name
        else:
            self.metadata['name'] = self.metadata['projectname']

        self.data = tempD['data']
        self.data['current_budget'] = tempD['data']['costcov']['cost']

        self.options = tempD['opt']

        program_set = {}
        program_set['name'] = 'Default'
        program_set['uuid'] = str(uuid.uuid4())
        program_set['programs'] = []
        for prog in self.metadata['programs']:
            program_set['programs'].append(program.Program.import_legacy(prog))
        self.program_sets.append(program_set)

        # Make the calibration - legacy files have one calibration
        # Using pop will remove them from the region so that downstream calls
        # will raise errors if they are not updated to use the new calibration
        c = {}
        c['uuid'] = str(uuid.uuid4())
        c['name'] = 'Default'
        c['const'] = self.D['P'].pop('const')
        c['hivprev'] = self.D['P'].pop('hivprev')
        c['popsize'] = self.D['P'].pop('popsize')
        c['pships'] = self.D['P'].pop('pships')
        c['transit'] = self.D['P'].pop('transit')
        c['metaparameters'] = self.D.pop('F')
        self.calibrations.append(c)

        # Go through the scenarios and convert them
        if 'scens' in tempD.keys():
            sbox = self.createsimbox('Scenarios')
            for scenario in tempD['scens']: # Separate cases in the web list 
                newsim = sim.SimParameter(scenario['scenario']['name'],self)
                for par in scenario['scenario']['pars']:
                    newsim.create_override(par['names'],par['pops'],par['startyear'],par['endyear'],par['startval'],par['endval'])
                sbox.simlist.append(newsim)

    def calibration_from_data(self,name='Data (auto)'):
        # Create a new calibration in the region corresponding to the data. This draws on code
        # from makedatapars

        def dataindex(dataarray, index):
            """ Take an array of data return either the first or last (...or some other) non-NaN entry """
            nrows = shape(dataarray)[0] # See how many rows need to be filled (either npops, nprogs, or 1)
            output = zeros(nrows) # Create structure
            for r in xrange(nrows): 
                output[r] = sanitize(dataarray[r])[index] # Return the specified index -- usually either the first [0] or last [-1]
            
            return output
        
        c = {}
        c['uuid'] = str(uuid.uuid4())
        c['name'] = name


        ## Key parameters - These were hivprev and pships, and are now in the calibration
        for parname in D['data']['key'].keys():
            c[parname] = dataindex(D['data']['key'][parname][0], 0) # Population size and prevalence -- # TODO: use uncertainties!
        
        # Matrices
        for parclass in ['pships', 'transit']:
            printv('Converting data parameter %s...' % parclass, 3, verbose)
            c[parclass] = D['data'][parclass]

        # Constants
        c['const'] = dict()
        for parclass in self.data['const'].keys():
            if type(self.data['const'][parclass])==dict: 
                c['const'][parclass] = dict()
                for parname in self.data['const'][parclass].keys():
                    c['const'][parclass][parname] = self.data['const'][parclass][parname][0] # Taking best value only, hence the 0
        
        ## !! unnormalizeF requires D.M...? But what if this is not in sync somehow?
        ## It's also unclear how this could work in the original code...
        ## This suggests that unnormalization of the metaparameters should be performed
        ## automatically inside the sim prior to running
        c['metaparameters'] = [dict() for s in xrange(D['opt']['nsims'])]
        for s in xrange(D['opt']['nsims']):
            span=0 if s==0 else 0.5 # Don't have any variance for first simulation
            c['metaparameters'][s]['init']  = perturb(D['G']['npops'],span)
            c['metaparameters'][s]['popsize'] = perturb(D['G']['npops'],span)
            c['metaparameters'][s]['force'] = perturb(D['G']['npops'],span)
            c['metaparameters'][s]['inhomo'] = zeros(D['G']['npops']).tolist()
            c['metaparameters'][s]['dx']  = perturb(4,span)
            #c['metaparameters'][s] = unnormalizeF(D['F'][s], D['M'], D['G'], normalizeall=True) # Un-normalize F
        self.calibrations.append(c)

    def save(self,filename):
        import dataio
        dataio.savedata(filename,self.todict())

    def todict(self):
        # Return a dictionary representation of the object for use with Region.fromdict()
        regiondict = {}
        regiondict['version'] = 1 # Could do something later by checking the version number

        regiondict['metadata'] = self.metadata 
        regiondict['data'] = self.data 
        regiondict['simboxlist'] = [sbox.todict() for sbox in self.simboxlist]
        regiondict['options'] = self.options # Populate default options here = self.options 
        regiondict['program_sets'] = [[1]] #self.program_sets 
        regiondict['calibrations'] = self.calibrations # Calibrations are stored as dictionaries
        regiondict['uuid'] = self.uuid 
        regiondict['D'] = self.D

        # BOC saving.
        regiondict['BOC_budgets'] = self.BOCx
        regiondict['BOC_objectives'] = self.BOCy    

        return regiondict

    def createsimbox(self, simboxname, isopt = False, createdefault = True):
        if isopt:
            self.simboxlist.append(SimBoxOpt(simboxname,self))
        else:
            self.simboxlist.append(SimBox(simboxname,self))
        if createdefault:
            self.simboxlist[-1].createsim(simboxname + '-default')
        return self.simboxlist[-1]
        
    def createsiminsimbox(self, simname, simbox):
        new_sim = simbox.createsim(simname)
        return new_sim
    
    # Runs through every simulation in simbox (if not processed) and processes them.
    # May optimise too depending on SimBox type.
    def runsimbox(self, simbox):
        simbox.runallsims(forcerun = False)
        
    # Runs through every simulation in simbox (if processed) and plots them, either multiplot or individual style.
    def plotsimbox(self, simbox, multiplot = False):
        if multiplot:
            simbox.viewmultiresults()
            if isinstance(simbox, SimBoxOpt):
                simbox.viewoptimresults(plotasbar = False)
                simbox.viewoptimresults(plotasbar = True)
        else:
            simbox.plotallsims()
            
###----------------------------------------------------------------------------
### GPA Methods
            
    # Method to generate a budget objective curve (BOC) for the Region.
    # Creates a temporary SimBoxOpt with a temporary SimBudget and calculates the BOC.
    # Ends by deleting the temporary objects and retaining BOC data.
    def developBOC(self, varfactors, forcecalc = False, extendresults = False):      
        if forcecalc or extendresults or not self.hasBOC():
            simbox = self.createsimbox(self.getregionname() + '-BOC-Calculations', isopt = True, createdefault = False)
            sim = self.createsiminsimbox(simbox.getname(), simbox)
            sim.run()   # Make sure simulation is processed, or 'financialanalysis' will not have its D['S'] component. Something to eventually change...
            try:
                testBOCx, testBOCy = sim.calculateeffectivenesscurve(varfactors)
                print("Region %s has calculated a Budget Objective Curve for..." % self.getregionname())
                print(varfactors)
            except:
                print("Region %s has failed to produce a Budget Objective Curve for..." % self.getregionname())
                print(varfactors)
            
            if extendresults:
                self.BOCx.extend(testBOCx)
                self.BOCy.extend(testBOCy)
            else:
                self.BOCx = testBOCx
                self.BOCy = testBOCy
            
            # Keeps the BOC sorted with respect to budget totals (i.e. the x axis).
            self.BOCx, self.BOCy = [list(a) for a in zip(*sorted(zip(self.BOCx, self.BOCy), key=lambda pair: pair[0]))]
            
            self.simboxlist.remove(simbox)      # Deletes temporary SimBoxOpt.
        else:
            print('Budget Objective Curve data already exists for region %s. Proceeding onwards...' % self.getregionname())
    
    # For now, this is just a complete recalculation of BOC data that already exists. In case you were originally optimising for 1 second or something.
    def recalculateBOC(self):
        if self.hasBOC():
            varfactors = self.converttotalstofactors(self.BOCx)
            
            self.developBOC(varfactors, forcecalc = True)
        else:
            print('Budget Objective Curve data does not seem to exist. Cannot refine.')
    
    # Returns spline for objective values achieved at different budget totals.
    def getBOCspline(self):
        try:
            return pchip(self.BOCx, self.BOCy, extrapolate=True)
        except:
            print('Budget Objective Curve data does not seem to exist...')
        
    def plotBOCspline(self):
        import matplotlib.pyplot as plt
        from numpy import linspace
        
        try:
            f = self.getBOCspline()
            x = linspace(min(self.BOCx), max(self.BOCx), 200)
            plt.plot(x,f(x),'-')
            plt.legend(['BOC'], loc='best')
            plt.show()
        except:
            print('Plotting of Budget Objective Curve failed!')
        
    def hasBOC(self):
        if len(self.BOCx) == 0 and len(self.BOCy) == 0:
            return False
        else:
            return True
    
    # Useful helper function to convert a summed alloc to a multiplicative factor, ignoring fixed costs.
    def converttotalstofactors(self, totals):
        print('Subtracting fixed costs from budget totals and converting to multiplicative factors...')
        print('A budget total equals non-fixed programs multiplied by the corresponding factor and added to fixed costs.')

        factors = []        
        defaultalloc = self.data['origalloc']        
        
        # Work out which programs don't have an effect and are thus fixed costs (e.g. admin).
        fixedtrue = [1.0]*(len(defaultalloc))
        for i in xrange(len(defaultalloc)):
            if len(self.metadata['programs'][i]['effects']): fixedtrue[i] = 0.0
        fixedtotal = sum([defaultalloc[i]*fixedtrue[i] for i in xrange(len(defaultalloc))])
        vartotal = sum([defaultalloc[i]*(1.0-fixedtrue[i]) for i in xrange(len(defaultalloc))])
        
        for total in totals:
            try:
                factor = (total-fixedtotal)/vartotal
            except:
                print('Divide-by-zero warning: The allocation sum of variable cost programs may be zero.')
                print('Returning a multiplicative budget factor of zero and continuing on...')
                factor = 0.0
            if factor < 0.0:
                print('Budget total $%f is less than the sum of the allocation fixed costs! Not possible.' % total)
                print('Returning a multiplicative budget factor of zero and continuing on...')
                factor = 0.0
            print('Returning a budget multiplication factor of %f for the budget total of $%f.' % (factor, total))
            factors.append(factor)
        
        return factors

###----------------------------------------------------------------------------       
        
    def printdata(self):
        print(self.data)
    
    def printmetadata(self):
        print(self.metadata)
        
    def printoptions(self):
        print(self.options)
        
    def printprograms(self):
        print(self.metadata['programs'])
        
    def printsimboxlist(self, assubset = False):
        # Prints with nice arrow formats if assubset is true. Otherwise numbers the list.        
        if assubset:
            if len(self.simboxlist) > 0:
                for simbox in self.simboxlist:
                    print(' --> %s%s' % (simbox.getname(), (" (optimisation container)" if isinstance(simbox, SimBoxOpt) else " (standard container)")))
                    simbox.printsimlist(assubsubset = True)
        else:
            if len(self.simboxlist) == 0:
                print('No simulations are currently associated with region %s.' % self.getregionname())
            else:
                print('Collections of simulations associated with this project...')
                fid = 0
                for simbox in self.simboxlist:
                    fid += 1
                    print('%i: %s%s' % (fid, simbox.getname(), (" (optimisation container)" if isinstance(simbox, SimBoxOpt) else " (standard container)")))
                    simbox.printsimlist(assubsubset = False)
                
    def setdata(self, data):
        self.data = data
        
    def getdata(self):
        return self.data
        
    def setmetadata(self, metadata):
        self.metadata = metadata
        
    def getmetadata(self):
        return self.metadata
        
    def setoptions(self, options):
        self.options = options
        
    def getoptions(self):
        return self.options
    
    def setprograms(self, programs):
        self.metadata['programs'] = programs
        
    def getprograms(self):
        return self.metadata['programs']
        
    def setregionname(self, regionname):
        self.metadata['name'] = regionname
        
    def getregionname(self):
        return self.metadata['name']
     
    def setorigalloc(self, alloc):
        self.data['origalloc'] = alloc
        
    def getorigalloc(self):
        return self.data['origalloc']

    def setD(self, D):
        self.D = D
        
    def getD(self):
        return self.D
        
    def makeworkbook(self,filename):
        """ Generate the Optima workbook -- the hard work is done by makeworkbook.py """
#        from printv import printv
        from dataio import templatepath
        import makeworkbook

        path = templatepath(filename)
        book = makeworkbook.OptimaWorkbook(filename, self.metadata['populations'], self.metadata['programs'], self.metadata['datastart'], self.metadata['dataend'])
        book.create(path)
        
    def loadworkbook(self,filename):
        """ Load an XSLX file into region.data """
        import loadworkbook

        # Note
        # 'data' is different depending on whether or not 'programs' is assigned below or not
        # Also, when loading Haiti.xlsx, the variable 'programs' below is different to
        # the contents of D['programs'] obtained by loading 'haiti.json'
        data, programs = loadworkbook.loadworkbook(filename)

        # For now, check that the uploaded programs are the same
        # In future, check region UUID
        if [x['name'] for x in programs] != [x['short_name'] for x in self.metadata['programs']]:
            raise Exception('The programs in the XLSX file do not match the region')

        # Save variables to region
        import updatedata
        self.metadata['programs'] = programs
        self.data = updatedata.getrealcosts(data)
        self.data['current_budget'] = self.data['costcov']['cost']
        
    def __repr__(self):
        return "Region %s ('%s')" % (self.uuid,self.metadata['name'])

    def get_popidx(self,shortname):
        # Return the index corresponding to a population shortname
        poplist = [x['short_name'] for x in self.metadata['populations']]

        if shortname == 'all':
            return len(poplist)+1
        else:
            try:
                popidx = poplist.index(shortname) + 1 # For some reason (frontend?) these indexes are 1-based rather than 0-based
            except:
                print 'Population "%s" not found! Valid populations are:' % (shortname)
                print poplist
                raise Exception('InvalidPopulation')
            return popidx
