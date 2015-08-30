from sim import Sim

class SimBudget2(Sim):

    def __init__(self, name, region,budget,calibration=None,programset=None):
        Sim.__init__(self, name, region,calibration)
        self.budget = budget # This contains spending values for all of the modalities for the simulation timepoints i.e. there are len(D['opt']['partvec']) spending values
        self.programset = programset if programset is not None else region.programsets[0].uuid # Use the first program set by default

        # Check that the program set exists
        if self.programset not in [x.uuid for x in region.programsets]:
            raise Exception('The provided program set UUID could not be found in the provided region')

    def todict(self):
        simdict = Sim.todict(self)
        simdict['type'] = 'SimBudget2'
        simdict['budget'] = self.budget
        simdict['programset'] = self.programset
        return simdict

    def load_dict(self,simdict):
        Sim.load_dict(self,simdict)
        self.budget = simdict['budget'] 
        self.programset = simdict['programset']

    def getprogramset(self):
        # Return a reference to the selected program set
        r = self.getregion()
        uuids = [x.uuid for x in r.programsets]
        return r.programsets[uuids.index(self.programset)]

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
        outcomes = programset.get_outcomes(self.budget)

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