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

    def makemodelpars(self):
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