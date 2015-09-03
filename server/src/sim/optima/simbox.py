from sim import Sim

import weakref
import uuid

#from scipy.interpolate import PchipInterpolator as pchip

class SimBox(object):
    def __init__(self, name, project):
        self.name = name
        self.simlist = []
        self.setproject(project)
        self.uuid = str(uuid.uuid4()) # Store UUID as a string - we just want a (practically) unique tag, no advanced functionality

    @classmethod
    def fromdict(SimBox,simboxdict,project):
        assert(simboxdict['project_uuid'] == project.uuid)
        simbox_type = globals()[simboxdict['type']]
        s = simbox_type(simboxdict['name'], project)
        s.setproject(project)
        s.load_dict(simboxdict)
        
        return s

    def load_dict(self, simboxdict):
        r = self.getproject()
        self.simlist = [Sim.fromdict(x,r) for x in simboxdict['simlist']]
        self.uuid = simboxdict['uuid'] # Loading a project restores the original UUID

    def todict(self):
        simboxdict = {}
        simboxdict['type'] = 'SimBox'
        simboxdict['name'] = self.name
        simboxdict['simlist'] = [s.todict() for s in self.simlist]
        simboxdict['project_uuid'] = self.getproject().uuid
        simboxdict['uuid'] = self.uuid

        return simboxdict
    
    def setproject(self,project):
        self.project = weakref.ref(project)

    def getproject(self):
        # self.project is a weakref object, which means to get
        # the project you need to do self.project() rather than
        # self.project. This function abstracts away this 
        # implementation detail in case it changes in future
        r = self.project()
        if r is None:
            raise Exception('The parent project has been garbage-collected and the reference is no longer valid')
        else:
            return r

    # Creates a simulation object but makes sure to initialise it immediately after, ready for processing.
    def createsim(self, simname):
        print('Preparing new basic simulation for standard container %s...' % self.name)
        self.simlist.append(Sim(simname,self.getproject()))
        self.simlist[-1].initialise()
        return self.simlist[-1]
        
    def runallsims(self, forcerun = False):
        for sim in self.simlist:
            if forcerun or not sim.isprocessed():
                sim.run()
                
    def plotallsims(self):
        for sim in self.simlist:
            if sim.isprocessed():
                sim.plotresults()

    # Needs to check processing like plotallsims.
    def viewmultiresults(self,show_wait=True):
        # Superimpose plots, like in the scenarios page in the frontend
        r = self.project()

        tempD = {}
        tempD['G'] = r.metadata

        Rarr = []
        atleastoneplot = False
        for sim in self.simlist:
            if sim.isprocessed():
                atleastoneplot = True
                tmp = {}
                tmp['R'] = sim.debug['results']
                tmp['label'] = sim.name
    
                Rarr.append(tmp)

        if not atleastoneplot:
            print('Not one simulation in this container is processed. No plot data exists.')
        else:
            import gatherplotdata, viewresults
            multidata = gatherplotdata.gathermultidata(tempD, Rarr,verbose=0)
            #viewmultiresults(M, whichgraphs={'prev':[1,1], 'plhiv':[0,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1], 'costcum':[1,1]}, simstartyear=2000, simendyear=2030, onefig=True, verbose=2, show_wait=False, linewidth=2):
            viewresults.viewmultiresults(multidata, show_wait = show_wait)

    def printsimlist(self, assubsubset = False):
        # Prints with long arrow formats if assubsubset is true. Otherwise uses short arrows.        
        if assubsubset:
            if len(self.simlist) > 0:
                for sim in self.simlist:
                    print('   --> %s%s' % (sim.getname(), (" (unprocessed)" if not sim.isprocessed() else " (processed)")))
        else:
            if len(self.simlist) == 0:
                print(' --> No simulations are currently stored in container %s.' % self.getname())
            else:
                for sim in self.simlist:
                    print(' --> %s%s' % (sim.getname(), (" (unprocessed)" if not sim.isprocessed() else " (processed)")))
        
    def setname(self, name):
        self.name = name
        
    def getname(self):
        return self.name

    def __repr__(self):
        return "SimBox %s ('%s')" % (self.uuid[0:8],self.name)

    def __getstate__(self):
        raise Exception('Simbox must be saved via a project')

    def __setstate__(self, state):
        raise Exception('Simboxes must be re-created via a project')
        