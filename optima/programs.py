"""
This module defines the Program and Programset classes, which are
used to define a single program/modality (e.g., FSW programs) and a
set of programs, respectively.

Version: 2017feb15
"""

from optima import Project, OptimaException, Link, odict, objrepr


class Programset(object):
    """
    Object to store all programs. Coverage-outcome data and functions belong to the program set, 
    while cost-coverage data/functions belong to the individual programs.
    """

    def __init__(self, name='default', parsetname=-1, project=None, programs=None):
        """ Initialize """
        if not isinstance(project, Project):
            errormsg = 'To create a program set, you must supply a project as an argument'
            raise OptimaException(errormsg)
        
        self.name = name
        self.programs = odict()
        self.covout = odict()
        self.parsetname = parsetname # Store the parset name
        self.projectref = Link(project) # Store pointer for the project, if available
        self.denominators = self.setdenominators() # Calculate the denominators for different coverage values
        if programs is not None: self.addprograms(programs)

    def __repr__(self):
        """ Print out useful information"""
        output = objrepr(self)
        output += '    Program set name: %s\n'    % self.name
        output += '            Programs: %s\n'    % self.programs.keys()
        output += '============================================================\n'
        return output
    
    def addprograms(self):
        ''' add a list of programs '''
        pass

    def rmprogram(self):
        ''' remove a program '''
        pass
    
    def addcovout(self):
        ''' add coverage-outcome parameter '''
        pass

    def defaultbudget(self):
        ''' get default budget '''
        pass

    def getbudget(self):
        ''' get budget from coverage '''
        pass

    def getcoverage(self):
        ''' get coverage from budget '''
        pass

    def reconcile(self):
        ''' reconcile with parset '''
        pass

    def compareoutcomes(self):
        ''' compare textually '''
        pass
    
    def check(self):
        ''' checks that all costcov and covout data is entered '''
        pass



class Program(object):
    ''' Defines a single program. '''
    
    def __init__(self, short=None, name=None, spend=None, basespend=None, coverage=None, unitcost=None, saturation=None, targetpops=None, targetpars=None):
        self.short = short # short name
        self.name = name # full name
        self.spend = spend # latest or estimated expenditure
        self.basespend = basespend # non-optimizable spending
        self.coverage = coverage # latest or estimated coverage (? -- not used)
        self.unitcost = unitcost # dataframe of [t, best, low, high]
        self.saturation = saturation # saturation coverage value
        self.targetpops = targetpops # key(s) for targeted populations
        self.targetpars = targetpars # which parameters are targeted



class Covout(object):
    ''' A coverage-outcome object -- cost-outcome objects are incorporated in programs '''
    
    def __init__(self, lowerlim=None, upperlim=None, progs=None):
        self.lowerlim = lowerlim
        self.upperlim = upperlim
        self.progs = odict()


class Val(object):
    ''' A single value for a coverage-outcome curve '''
    
    def __init__(self, best=None, low=None, high=None):
        self.best = best
        self.low = low
        self.high = high
        self.dist = 
