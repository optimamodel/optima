from sim import Sim
import numpy

class SimBudget2(Sim):

    def __init__(self, name, region,budget,calibration=None,programset=None):
        Sim.__init__(self, name, region,calibration)
        self.budget = budget # This contains spending values for all of the modalities for the simulation timepoints i.e. there are len(D['opt']['partvec']) spending values
        self.programset = programset if programset is not None else region.programsets[0].uuid # Use the first program set by default
        self.popsizes = {} # Estimates for the population size obtained by running a base Sim within the parent region

        # Check that the program set exists
        if self.programset not in [x.uuid for x in region.programsets]:
            raise Exception('The provided program set UUID could not be found in the provided region')

    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimBudget2'
        simdict['budget'] = self.budget
        simdict['programset'] = self.programset
        simdict['popsizes'] = self.popsizes
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.budget = simdict['budget'] 
        self.programset = simdict['programset']
        self.programset = simdict['programset']
        self.popsizes = simdict['popsizes']

    def getprogramset(self):
        # Return a reference to the selected program set
        r = self.getregion()
        uuids = [x.uuid for x in r.programsets]
        return r.programsets[uuids.index(self.programset)]

    def get_estimated_popsizes(self,artindex=None):
        # This function populates self.popsizes which is used in self.makemodelpars() to convert
        # fractions of populations (coverage) into actual numbers of people
        # This function generates a dict like {'FSW':[1 1.1 1.2...],'....'} where the keys are different
        # population breakdowns, and the values are arrays of number of people for each time in 
        # region.options['partvec']
        #
        # Available populations are
        #   - All of the populations listed in r.metadata['inputpopulations'] (access by short name)
        #   - total
        # And then the numbers of people reached by the following program names
        #   - aidstest, numost, sharing, numpmtct, breast, numfirstline, numsecondline, numcircum
        self.popsizes = {}
        r = self.getregion()
        s = Sim('temp',r,self.calibration) # Make a base sim with the selected calibration
        DS = s.run() # Retrieve D.S
        people = DS['people']

        # Define indexes for various breakdowns
        pops = [x['short_name'] for x in r.metadata['inputpopulations']]
        injects = numpy.array([x['injects'] for x in r.metadata['inputpopulations']])
        ismale  = numpy.array([x['male'] for x in r.metadata['inputpopulations']])
        aidstested = numpy.array(range(27,31)) # WARNING - this assumes particular indexes for the relevant health states!
        if artindex is None:
            artindex = range(1,r.metadata['nstates']) # Choose a sensible default here - here it is all states except the first

        # Calculate the population sizes
        for i in xrange(len(pops)): # Iterate over the populations
            self.popsizes[pops[i]] = people[:,i,:].sum(axis=(0))

        self.popsizes['total'] = people.sum(axis=(0,1))
        self.popsizes['aidstest'] = people[aidstested,:,:].sum(axis=(0,1)) 
        self.popsizes['numost'] = people[:,injects,:].sum(axis=(0,1))
        self.popsizes['sharing'] = self.popsizes['numost']
        self.popsizes['numpmtct'] = numpy.cumsum(numpy.multiply(s.parsmodel['birth'][:,:]*r.options['dt'], people[artindex,:,:].sum(axis=0)).sum(axis=0))
        self.popsizes['breast'] = numpy.multiply(s.parsmodel['birth'][:,:], s.parsmodel['breast'][:], people[artindex,:,:].sum(axis=0)).sum(axis=0)
        self.popsizes['numfirstline'] = people[artindex,:,:].sum(axis=(0,1))
        self.popsizes['numsecondline'] = self.popsizes['numfirstline']
        self.popsizes['numcircum'] = people[:,ismale,:].sum(axis = (0,1))

    def initialize(self):
        # Need to make a temporary sim, and then use makemodelpars
        # temporary sim should be created here, because optimization will
        # call makemodelpars() many times, but the temporary sim from 
        # data pars won't change. Could consider just storing the output instead
        # of storing the whole sim?
        return

    def makemodelpars(self,perturb=False):
        # If perturb == True, then a random perturbation will be applied at the CCOC level
        r = self.getregion()
        npts = len(r.options['partvec']) # Number of time points

        programset = self.getprogramset()
        outcomes = programset.get_outcomes(self.budget,perturb)

        for i in xrange(0,len(prog.effects['param'])): # For each of the effects
            if prog.effects['iscoverageparam'][i]:
                P[prog.effects['param'][i]]['c'][:] = outcomes[i]
            else:
                popnumber = r.get_popidx(prog.effects['popname'][i])-1 # Yes, get_popidx is 1-based rather than 0 based...cf. scenarios
                P[prog.effects['param'][i]]['c'][popnumber] = outcomes[i]

        from makemodelpars import makemodelpars
        self.parsmodel = makemodelpars(P, r.options, withwhat='c')

    def __repr__(self):
        return "SimBudget2 %s ('%s')" % (self.uuid,self.name)  


def gettargetpop(D=None, artindex=None, progname=None):
    ''' Calculate target population for a given program'''
    
    from numpy import cumsum
    
    # Sort out time vector and indexing
    tvec = arange(D['G']['datastart'], D['G']['dataend']+D['opt']['dt'], D['opt']['dt']) # Extract the time vector from the sim
    npts = len(tvec) # Number of sim points

    # Figure out the targeted population(s) 
    prognumber = D['data']['meta']['progs']['short'].index(progname) # get program number
    targetpops = []
    targetpars = []
    popnumbers = []
    for effect in D['programs'][prognumber]['effects']:
        targetpops.append(effect['popname'])
        targetpars.append(effect['param'])
        if effect['popname'] in D['data']['meta']['pops']['short']:
            popnumbers.append(D['data']['meta']['pops']['short'].index(effect['popname']))
    targetpops = list(set(targetpops))
    targetpars = list(set(targetpars))
    popnumbers = list(set(popnumbers))

    targetpopmodel = None

    # Figure out the total model-estimated size of the targeted population(s)
    for thispar in targetpars: # Loop through parameters
        if D['P'].get(thispar):
            if len(D['P'][thispar]['p'])==D['G']['npops']: # For parameters whose effect is differentiated by population, we add up the targeted populations
                targetpopmodel = D['S']['people'][:,popnumbers,0:npts].sum(axis=(0,1))
            elif len(D['P'][thispar]['p'])==1: # For parameters whose effects are not differentiated by population, we make special cases depending on the parameter
                if thispar == 'aidstest': # Target population = diagnosed PLHIV, AIDS stage
                    targetpopmodel = D['S']['people'][27:31,:,0:npts].sum(axis=(0,1))
                elif thispar in ['numost','sharing']: # Target population = the sum of all populations that inject
                    injectindices = [i for i, x in enumerate(D['data']['meta']['pops']['injects']) if x == 1]
                    targetpopmodel = D['S']['people'][:,injectindices,0:npts].sum(axis = (0,1))
                elif thispar == 'numpmtct': # Target population = HIV+ pregnant women
                    targetpopmodel = cumsum(multiply(D['M']['birth'][:,0:npts]*D['opt']['dt'], D['S']['people'][artindex,:,0:npts].sum(axis=0)).sum(axis=0))
                elif thispar == 'breast': # Target population = HIV+ breastfeeding women
                    targetpopmodel = multiply(D['M']['birth'][:,0:npts], D['M']['breast'][0:npts], D['S']['people'][artindex,:,0:npts].sum(axis=0)).sum(axis=0)
                elif thispar in ['numfirstline','numsecondline']: # Target population = diagnosed PLHIV
                    targetpopmodel = D['S']['people'][artindex,:,0:npts].sum(axis=(0,1))
                elif thispar == 'numcircum': # Target population = men (??)
                    maleindices = findinds(D['data']['meta']['pops']['male'])
                    targetpopmodel = D['S']['people'][:,maleindices,0:npts].sum(axis = (0,1))
            else:
                print('WARNING, Parameter %s of odd length %s' % (thispar, len(D['P'][thispar]['p'])))
        else:
            print('WARNING, Unrecognized parameter %s' % thispar)
    if len(targetpars)==0:
        print('WARNING, no target parameters for program %s' % progname)
                
    # We only want the model-estimated size of the targeted population(s) for actual years, not the interpolated years
    yearindices = range(0,npts,int(1/D['opt']['dt']))
    
    targetpop = None
    if targetpopmodel is not None:
        targetpop = targetpopmodel[yearindices]

    return targetpop





def getcoverage(D, alloc=None, randseed=None):
    ''' Get the coverage levels corresponding to a particular allocation '''
    from numpy import zeros_like, array, isnan
    from makeccocs import cc2eqn, cceqn, gettargetpop
    from utils import perturb
    
    allocwaslist = 0
    if isinstance(alloc,list): alloc, allocwaslist = array(alloc), 1
    coverage = {}
    coverage['num'], coverage['per'] = zeros_like(alloc), zeros_like(alloc)

    for prognumber, progname in enumerate(D['data']['meta']['progs']['short']):
        if D['programs'][prognumber]['effects']:            

            targetpop = gettargetpop(D=D, artindex=range(D['G']['nstates'])[1::], progname=progname)[-1]
            program_ccparams = D['programs'][prognumber]['convertedccparams']
            use_default_ccparams = not program_ccparams or (not isinstance(program_ccparams, list) and isnan(program_ccparams))
            if not use_default_ccparams:
                convertedccparams = D['programs'][prognumber]['convertedccparams'] 
            else:
                convertedccparams = setdefaultccparams(progname=progname)
            if randseed>=0: convertedccparams[0][1] = array(perturb(1,(array(convertedccparams[2][1])-array(convertedccparams[1][1]))/2., randseed=randseed)) - 1 + array(convertedccparams[0][1]) 
            coverage['per'][prognumber,] = cc2eqn(alloc[prognumber,], convertedccparams[0]) if len(convertedccparams[0])==2 else cceqn(alloc[prognumber,], convertedccparams[0])
            coverage['num'][prognumber,] = coverage['per'][prognumber,]*targetpop
        else:
            coverage['per'][prognumber,] = array([None]*len(alloc[prognumber,]))
            coverage['num'][prognumber,] = array([None]*len(alloc[prognumber,]))

    if allocwaslist:
        coverage['num'] = coverage['num'].tolist()
        coverage['per'] = coverage['per'].tolist()
            
    return coverage