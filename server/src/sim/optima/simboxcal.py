from simbox import SimBox

import uuid
from numpy import zeros
from liboptima.utils import perturb, dataindex,printv

# A container for calibrating Sims.
class SimBoxCal(SimBox):
    def __init__(self,name,region):
        SimBox.__init__(self,name,region)
        
    def load_dict(self, simboxdict):
        SimBox.load_dict(self,simboxdict)
       
    def todict(self):
        simboxdict = SimBox.todict(self)
        simboxdict['type'] = 'SimBoxCal'    # Overwrites SimBox type.
        
        return simboxdict

    # Create a new calibration in the region storing this SimBoxCal corresponding to its data.
    # This code is drawn from legacy makedatapars.
    def calibratefromdefaultdata(self, name='Data (auto)', verbose=2):

        r = self.getregion()
        
        c = {}
        c['uuid'] = str(uuid.uuid4())
        c['name'] = name

        ## Key parameters - These were hivprev and pships, and are now in the calibration
        for parname in r.data['key'].keys():
            c[parname] = dataindex(r.data['key'][parname][0], 0) # Population size and prevalence -- # TODO: use uncertainties!
        
        # Matrices
        for parclass in ['pships', 'transit']:
            printv('Converting data parameter %s...' % parclass, 3, verbose)
            c[parclass] = r.data[parclass]

        # Constants
        c['const'] = dict()
        for parclass in r.data['const'].keys():
            if type(r.data['const'][parclass])==dict: 
                c['const'][parclass] = dict()
                for parname in r.data['const'][parclass].keys():
                    c['const'][parclass][parname] = r.data['const'][parclass][parname][0] # Taking best value only, hence the 0
        
        ## !! unnormalizeF requires D.M...? But what if this is not in sync somehow?
        ## It's also unclear how this could work in the original code...
        ## This suggests that unnormalization of the metaparameters should be performed
        ## automatically inside the sim prior to running
        ##
        ## I guess this is either where makemodelpars or makedatapars will be run on the encapsulated default Sim...
        c['metaparameters'] = [dict() for s in xrange(r.options['nsims'])]
        for s in xrange(r.options['nsims']):
            span=0 if s==0 else 0.5 # Don't have any variance for first simulation
            c['metaparameters'][s]['init']  = perturb(len(r.metadata['populations']),span)
            c['metaparameters'][s]['popsize'] = perturb(len(r.metadata['populations']),span)
            c['metaparameters'][s]['force'] = perturb(len(r.metadata['populations']),span)
            c['metaparameters'][s]['inhomo'] = zeros(len(r.metadata['populations'])).tolist()
            c['metaparameters'][s]['dx']  = perturb(4,span)
            #c['metaparameters'][s] = unnormalizeF(D['F'][s], D['M'], D['G'], normalizeall=True) # Un-normalize F
        r.calibrations.append(c)
        

    def __repr__(self):
        return "SimBoxCal %s ('%s')" % (self.uuid[0:8],self.name)