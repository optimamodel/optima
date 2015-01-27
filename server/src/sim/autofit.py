def autofit(D, timelimit=60, simstartyear=2000, simendyear=2015, verbose=2):
    """
    Automatic metaparameter fitting code:
        D is the project data structure
        timelimit is the maximum time limit for fitting in seconds
        simstartyear is the year to begin running the model
        simendyear is the year to stop running the model
        verbose determines how much information to print.
        
    Version: 2014nov30 by cliffk
    """
    from numpy import mean, array
    from model import model
    from printv import printv
    from ballsd import ballsd
    from bunch import Bunch as struct
    from utils import findinds
    eps = 0.01 # Don't use too small of an epsilon to avoid divide-by-almost zero errors -- this corresponds to 1% which is OK as an absolute error for prevalence
    printv('Running automatic calibration...', 1, verbose)
    
    # Set options to update year range
    from setoptions import setoptions
    D.opt = setoptions(D.opt, simstartyear=simstartyear, simendyear=simendyear)
    
    def errorcalc(Flist):
        """ Calculate the error between the model and the data """
        
        printv(Flist, 4, verbose)
        
        F = list2dict(D.F[0], Flist)
        S = model(D.G, D.M, F, D.opt, verbose=verbose)
        
        # Pull out diagnoses data
        dx = [struct()]
        dx[0].data = struct()
        dx[0].model = struct()
        dx[0].data.x, dx[0].data.y = extractdata(D.G.datayears, D.data.opt.numdiag[0])
        dx[0].model.x = D.opt.tvec
        dx[0].model.y = S.dx.sum(axis=0)
        
        # Prevalence data
        prev = [struct() for p in range(D.G.npops)]
        for p in range(D.G.npops): 
            prev[p].data = struct()
            prev[p].model = struct()
            prev[p].data.x, prev[p].data.y = extractdata(D.G.datayears, D.data.key.hivprev[0][p]) # The first 0 is for "best"
            prev[p].model.x = D.opt.tvec
            prev[p].model.y = S.people[1:,p,:].sum(axis=0) / S.people[:,p,:].sum(axis=0) # This is prevalence
        
        mismatch = 0
        for base in [dx, prev]:
            for ind in range(len(base)):
                for y,year in enumerate(base[ind].data.x):
                    modelind = findinds(D.opt.tvec, year)
                    if len(modelind)>0: # TODO Cliff check
                        mismatch += abs(base[ind].model.y[modelind] - base[ind].data.y[y]) / mean(base[ind].data.y+eps)

        return mismatch

    # Convert F to a flast list for the optimization algorithm
    Forig = array(dict2list(D.F[0]))
    
    # Run the optimization algorithm
    Fnew, fval, exitflag, output = ballsd(errorcalc, Forig, xmin=0*Forig, xmax=100*Forig, timelimit=timelimit, verbose=verbose)
    
    # Update the model, replacing F
    D.F = [list2dict(D.F[0], Fnew)]
    D.S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
    allsims = [D.S]
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(D, allsims, D.opt.quantiles, verbose=verbose)

    # Gather plot data
    from gatherplotdata import gatheruncerdata
    D.plot.E = gatheruncerdata(D, D.R, verbose=verbose)
    
    printv('...done with automatic calibration.', 2, verbose)
    return D
    


def dict2list(Fdict):
    """
    Convert the F dictionary to a flat list of parameters. Do it manually to 
    be sure the keys are in the right order.
    """
    Flist = []
    for key in ['init','popsize', 'force','dx']:
        this = Fdict[key]
        for i in range(len(this)):
            Flist.append(Fdict[key][i])
    return Flist



def list2dict(Forig, Flist):
    """
    Convert the list Flist into a dictionary Fdict.
    """
    from copy import deepcopy
    Fdict = deepcopy(Forig)
    Flist = Flist.tolist()
    for key in ['init','popsize', 'force','dx']:
        for i in range(len(Fdict[key])):
            Fdict[key][i] = Flist.pop(0)
    return Fdict




def extractdata(xdata, ydata):
    """ Return the x and y data values for non-nan y data """
    from numpy import isnan, array
    nonnanx = array(xdata)[~isnan(array(ydata))]
    nonnany = array(ydata)[~isnan(array(ydata))]
    return nonnanx, nonnany
