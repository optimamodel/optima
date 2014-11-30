def autofit(D, timelimit=60, startyear=2000, endyear=2015, verbose=2):
    """
    Automatic metaparameter fitting code:
        D is the project data structure
        timelimit is the maximum time limit for fitting in seconds
        startyear is the year to begin running the model
        endyear is the year to stop running the model
        verbose determines how much information to print.
        
    Version: 2014nov30 by cliffk
    """
    
    from model import model
    from printv import printv
    from ballsd import ballsd
    printv('Running automatic calibration...', 1, verbose)
    
    
    def errorcalc(F):
        """ Calculate the error between the model and the data """
        S = model(D.G, D.M, F, D.opt, verbose=verbose)
        
        
        
        foo = S.sum()
        
        return mismatch

    # Convert F to a flast list for the optimization algorithm
    Forig = dict2list(D.F[0])
    
    # Run the optimization algorithm
    Fnew, fval, exitflag, output = ballsd(errorcalc, Forig, timelimit=timelimit)
    
    # Update the model
    D.F[0] = list2dict(D.F, Fnew)
    D.S = model(D.G, D.M, D.F[0], D.opt, verbose=verbose)
    allsims = [D.S]
    
    # Calculate results
    from makeresults import makeresults
    D.R = makeresults(D, allsims, D.opt.quantiles, verbose=verbose)

    # Gather plot data
    from gatherplotdata import gatherepidata
    D.plot.E = gatherepidata(D, D.R, verbose=verbose)
    
    printv('...done with automatic calibration.', 2, verbose)
    return D
    


def dict2list(Fdict):
    """
    Convert the F dictionary to a flat list of parameters. Do it manually to 
    be sure the keys are in the right order.
    """
    Flist = []
    for key in ['init','force','dx','tx1','tx2']:
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
    for key in ['init','force','dx','tx1','tx2']:
        for i in range(len(Fdict[key])):
            Fdict[key][i] = Flist.pop(0)
    return Fdict