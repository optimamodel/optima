def autofit(D, timelimit=None, maxiters=500, simstartyear=2000, simendyear=2015, verbose=5):
    """
    Automatic metaparameter fitting code:
        D is the project data structure
        timelimit is the maximum time limit for fitting in seconds
        maxiters is the maximum number of iterations
        simstartyear is the year to begin running the model
        simendyear is the year to stop running the model
        verbose determines how much information to print.
        
    Version: 2015jan31 by cliffk
    """
    #import pdb
    from numpy import mean, array
    from model import model
    from printv import printv
    from ballsd import ballsd
    from bunch import Bunch as struct
    from utils import findinds
    from copy import deepcopy
    from updatedata import normalizeF, unnormalizeF
    eps = 0.01 # Don't use too small of an epsilon to avoid divide-by-almost zero errors -- this corresponds to 1% which is OK as an absolute error for prevalence
    printv('Running automatic calibration...', 1, verbose)
    origM = deepcopy(D.M)
    origG = deepcopy(D.G)
    
    # Set options to update year range
    from setoptions import setoptions
    D.opt = setoptions(D.opt, simstartyear=simstartyear, simendyear=simendyear)
    
    #pdb.set_trace()    
    
    def errorcalc(Flist):
        """ Calculate the error between the model and the data """
        
        printv(Flist, 4, verbose)
        
        F = list2dict(D.F[0], Flist)
        F = unnormalizeF(F, origM, origG) # CK: Convert from normalized to unnormalized F (NB, Madhura)
        S = model(D.G, D.M, F, D.opt, verbose=verbose)
        
        # Pull out Prevalence data
        prev = [struct() for p in range(D.G.npops)]
        for p in range(D.G.npops): 
            prev[p].data = struct()
            prev[p].model = struct()
            prev[p].data.x, prev[p].data.y = extractdata(D.G.datayears, D.data.key.hivprev[0][p]) # The first 0 is for "best"
            prev[p].model.x = S.tvec
            prev[p].model.y = S.people[1:,p,:].sum(axis=0) / S.people[:,p,:].sum(axis=0) # This is prevalence      
                                                        
        #indicators = struct()
        #indicatorkeys = ['death', 'newtreat', 'numtest','numinfect', 'dx']
        #datakeys = ['death', 'newtreat', 'numtest','numinfect', 'dx']
        for key in indicatorkeys:
            indicators[key] = struct()
        [death, newtreat, numtest, numinfect, dx] = [[struct()], [struct()], [struct()], [struct()], [struct()]]        
        
        # Pull out other indicators data
        mismatch = 0
        allmismatches = []
        for base in [death, newtreat, numtest, numinfect, dx]:
            base[0].data = struct()
            base[0].model = struct()
            base[0].model.x = S.tvec
            if base == death:
                base[0].data.x, base[0].data.y = extractdata(D.G.datayears, D.data.opt.death[0])
                base[0].model.y = S.death.sum(axis=0)
            elif base == newtreat:
                base[0].data.x, base[0].data.y = extractdata(D.G.datayears, D.data.opt.newtreat[0])
                base[0].model.y = S.newtx1.sum(axis=0) + S.newtx2.sum(axis=0)
            elif base == numtest:
                base[0].data.x, base[0].data.y = extractdata(D.G.datayears, D.data.opt.numtest[0])
                base[0].model.y = D.M.hivtest.sum(axis=0)*S.people.sum(axis=0).sum(axis=0) #testing rate x population
            elif base == numinfect:
                base[0].data.x, base[0].data.y = extractdata(D.G.datayears, D.data.opt.numinfect[0])
                base[0].model.y = S.inci.sum(axis=0)
            elif base == dx:
                base[0].data.x, base[0].data.y = extractdata(D.G.datayears, D.data.opt.numdiag[0])
                base[0].model.y = S.dx.sum(axis=0)

        for base in [death, newtreat, numtest, numinfect, dx, prev]:
            for ind in range(len(base)):
                for y,year in enumerate(base[ind].data.x):
                    modelind = findinds(S.tvec, year)
                    if len(modelind)>0: # TODO Cliff check
                        thismismatch = abs(base[ind].model.y[modelind] - base[ind].data.y[y]) / mean(base[ind].data.y+eps)
                        allmismatches.append(thismismatch)
                        mismatch += thismismatch
        printv('Current mismatch: %s' % array(thismismatch).flatten(), 5, verbose=verbose)
        return mismatch

    # Convert F to a flast list for the optimization algorithm
    Forig = normalizeF(D.F[0], origM, origG) # CK: Convert from normalized to unormalized F (NB, Madhura)
    Forig = array(dict2list(Forig)) # Convert froma  dictionary to a list
    
    #pdb.settrace()
    # Run the optimization algorithm
    Fnew, fval, exitflag, output = ballsd(errorcalc, Forig, xmin=0*Forig, xmax=100*Forig, timelimit=timelimit, MaxIter=maxiters, verbose=verbose)
    
    # Update the model, replacing F
    Fnew = list2dict(D.F[0], Fnew) # Convert from list to dictionary
    Fnew = unnormalizeF(Fnew, origM, origG) # CK: Convert from normalized to unormalized F (NB, Madhura)
    D.F = [Fnew] # Store dictionary in list
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
    for key in ['init', 'force']:
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
    for key in ['init', 'force']:
        for i in range(len(Fdict[key])):
            Fdict[key][i] = Flist.pop(0)
    return Fdict


#%%


def extractdata(xdata, ydata):
    """ Return the x and y data values for non-nan y data """
    from numpy import isnan, array
    nonnanx = array(xdata)[~isnan(array(ydata))]
    nonnany = array(ydata)[~isnan(array(ydata))]
    return nonnanx, nonnany
