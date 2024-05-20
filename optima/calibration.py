"""
CALIBRATION

Function(s) to perform calibration.
"""

from optima import OptimaException, Link, Par, dcp, asd, printv, findinds, isnumber, odict
from numpy import zeros, array, mean

import six
if six.PY3:
    unicode = str

__all__ = ['autofit']

def autofit(project=None, name=None, fitwhat=None, fitto=None, method='wape', maxtime=None, maxiters=1000, verbose=2, doplot=False, randseed=None, **kwargs):
    ''' 
    Function to automatically fit parameters. Parameters:
        fitwhat = which parameters to vary to improve the fit; these are defined in parameters.py under the 'auto' attribute; default is 'force' (FOI metaparameters only)
        fitto = what kind of data to fit to; options are anything in results.main; default is 'prev' (prevalence) or everything
        method = which method of calculating the objective/goodness-of-fit to use; default weighted absolute percentage error to place less weight on outliers
    Others should be self-explanatory.
    
    Version: 2017may22 
    '''
    if doplot: # Store global information for debugging
        global autofitfig, autofitresults
        autofitfig, autofitresults = [None]*2
    
    timestr = 'unlimited' if maxtime is None else str(maxtime)
    itersstr = 'unlimited' if maxiters is None else str(maxiters)
    printv('Performing automatic fitting for %s seconds/%s iterations...' % (timestr,itersstr), 1, verbose)
    
    # Validate input
    if project is None: raise OptimaException('autofit() requires a project in order to run')
    if name is None: name = -1 # Calibrate last parameter set
    elif type(name) not in (str,unicode) and not(isnumber(name)): raise OptimaException('%s must be the name or index of a parameter set' % name)
    
    # Initialization
    parset = project.parsets[name] # Shorten the original parameter set
    parset.projectref = Link(project) # Try to link the parset back to the project
    pars = dcp(parset.pars) # Just get a copy of the pars for parsing
    if fitwhat is None: fitwhat = ['force'] # By default, automatically fit force-of-infection only
    if type(fitwhat)==str: fitwhat = [fitwhat]
    if type(fitto)==str: fitto = [fitto]
    parset.improvement = [] # For storing the improvement for each fit
    
    # Create the list of parameters to be fitted and set the limits
    parlist = makeparlist(pars, fitwhat)
    parlower  = array([item['limits'][0] for item in parlist])
    parhigher = array(project.settings.convertlimits([item['limits'][1] for item in parlist])) # Replace text labels with numeric values
    
    # Perform fit
    parvec = convert(pars, parlist)
    args = {'pars':pars, 'parlist':parlist, 'project':project, 'fitto':fitto, 'method':method, 'doplot':doplot, 'verbose':verbose}
    res = asd(objectivecalc, parvec, args=args, xmin=parlower, xmax=parhigher, maxtime=maxtime, maxiters=maxiters, randseed=randseed, verbose=verbose, **kwargs)

    # Save, along with some additional info
    pars = convert(pars, parlist, res.x)
    parset.pars = pars
    parset.improvement.append(res.details.fvals) # Store improvement history
    parset.autofitsettings = odict([('fitwhat', fitwhat), ('fitto', fitto), ('maxtime', maxtime), ('maxiters', maxiters), ('randseed', randseed)])
    
    return parset



## WARNING -- the following two functions must be updated together! 

# Populate lists of what to fit
def makeparlist(pars, fitwhat):
    ''' 
    This uses the "manual" attribute to decide what to calibrate (e.g., just the metaparameter
    or all the values.
    
    "fitwhat" options (see parameters.py, especially listparattributes()): 
    ['init','popsize','test','treat','force','other','const']
    '''
    parlist = []
    for parname in pars: # Just use first one, since all the same
        par = pars[parname]
        if issubclass(type(par), Par): # Check if it's a parameter
            if par.short in fitwhat: # It's in the list of things to fit
                if par.manual =='meta':
                    parlist.append({'name':par.short, 'type':par.manual, 'limits':par.limits, 'ind':None})
                elif par.manual =='pop':
                    for i in range(len(par.y)): parlist.append({'name':par.short, 'type':par.manual, 'limits':par.limits, 'ind':i})
                elif par.manual =='exp':
                    for i in range(len(par.i)): parlist.append({'name':par.short, 'type':par.manual, 'limits':par.limits, 'ind':i})
                elif par.manual =='const' or par.manual =='year':
                    parlist.append({'name':par.short, 'type':par.manual, 'limits':par.limits, 'ind':None})
                else:
                    raise OptimaException('Parameter "manual" type "%s" not understood' % par.manual)
        else: pass # It's like popkeys or something -- don't worry, be happy
    return parlist


def convert(pars, parlist, parvec=None):
    ''' 
    If parvec is not supplied:
        Take a parameter set (e.g. P.parsets[0].pars), a list of "types" 
        (e.g. 'force'), and a list of keys (e.g. 'hivtest'), and return a
        vector of values, e.g. "dehydrate" them.
    
    If parvec is supplied:
        Take a vector of parameter values and "hydrate" them into a pars object
        using a list of "types" (e.g. 'force'), and a list of keys (e.g. 'hivtest').
    
    Relies on the structure of makeparlist() above...
    '''
    
    # Handle inputs
    nfitpars = len(parlist)
    if parvec is None: 
        tv = True # to vector
        parvec = zeros(nfitpars)
    else: tv = False
    
    # Do the loop
    for i in range(nfitpars):
        thistype = parlist[i]['type'] # Should match up with par.manual
        thisname = parlist[i]['name']
        thisind = parlist[i]['ind']
        if thistype in ['force', 'pop']: 
            if tv: parvec[i] = pars[thisname].y[thisind]
            else:  pars[thisname].y[thisind] = parvec[i]
        elif thistype=='exp': 
            if tv: parvec[i] = pars[thisname].m # Don't change growth rates, change metaparameter instead (mostly influencing first data point)
            else:  pars[thisname].m = parvec[i]
        elif thistype=='meta': 
            if tv: parvec[i] = pars[thisname].m
            else:  pars[thisname].m = parvec[i]
        elif thistype=='const': 
            if tv: parvec[i] = pars[thisname].y
            else:  pars[thisname].y = parvec[i]
        else: raise OptimaException('Parameter type "%s" not understood' % thistype)
    
    # Decide which to return
    if tv: return parvec
    else:  return pars


def extractdata(xdata, ydata):
    ''' Return the x and y data values for non-nan y data '''
    from numpy import isnan, array
    nonnanx = array(xdata)[~isnan(array(ydata))]
    nonnany = array(ydata)[~isnan(array(ydata))]
    return nonnanx, nonnany


def objectivecalc(parvec=None, pars=None, parlist=None, project=None, fitto='prev', method='wape', bestindex=0, doplot=False, verbose=2):
    ''' 
    Calculate the mismatch between the model and the data -- may or may not be
    related to the likelihood. Either way, it's very uncertain what this function
    does.
    
    TODO: replace 'bestindex' with upper and lower limits for the data
    '''
    
    if doplot: # Store global information for debugging -- TODO, consider better ways of doing this
        global autofitfig, autofitresults
        from pylab import figure, ceil, sqrt, subplot, scatter, xlabel, ylabel, plot, show, pause, ylim, bar, arange
        if autofitfig is None: 
            autofitfig = figure(figsize=(16,12), facecolor=(1,1,1))
            autofitfig.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.95, wspace=0.3, hspace=0.4)
        if autofitresults is None: autofitresults = {'count':[], 'mismatch':[], 'allmismatches':[]}
    
    # Validate input -- check everything in one go
    if any([arg is None for arg in [parvec, pars, parlist, project]]): 
        raise OptimaException('objectivecalc() requires parvec, pars, parlist, and project inputs')
    
    eps = project.settings.eps # Specify absolute error -- can't be larger than ~0.001 because then general population prevalence might be weighted incorrectly
    pars = convert(pars, parlist, parvec)
    results = project.runsim(pars=pars, start=project.data['years'][0], end=project.data['years'][-1], verbose=0, resultname=project.name+'-autofit', addresult=False)
    
    ## Loop over all results
    allmismatches = []
    count = 0
    mismatch = 0
    if doplot: debugdata = []
    if fitto in [None, 'all', ['all']]: fitto = list(results.main.keys()) # If not specified, use everything
    for key in fitto: # The results! e.g. key='prev'
        try: this = results.main[key]
        except: 
            errormsg = 'autofit(): Key to fit "%s" not found; valid keys are:\n%s' % (key, results.main.keys())
            raise OptimaException(errormsg)
        for attr in ['tot', 'pops']: # Loop over either total or by population denominators
            tmpdata = getattr(this, 'data'+attr) # Get this data, e.g. results.main['prev'].datatot
            if tmpdata is not None: # If it actually exists, proceed
                tmpmodel = getattr(this, attr) # Get this result, e.g. results.main['prev'].tot
                datarows = tmpdata[bestindex] # Pull out data without uncertainty
                modelrows = tmpmodel[bestindex] # Pull out just the best result (likely only 1 index) -- TODO: check if should be another index
                nrows = len(datarows)
                for row in range(nrows): # Loop over each available row
                    datarow = datarows[row]
                    if len(modelrows.shape)>1: modelrow = modelrows[row]
                    else:                      modelrow = modelrows
                    datax, datay = extractdata(results.datayears, datarow) # Pull out the not-NaN values
                    if doplot: rowname = 'total' if nrows==1 else pars['popkeys'][row]
                    for i,year in enumerate(datax): # Loop over each data point available
                        count += 1
                        modelx = findinds(results.tvec, year) # Find the index of the corresponding time point
                        modely = modelrow[modelx] # Finally, extract the model result!
                        if   method=='wape': thismismatch = abs(modely - datay[i]) / mean(datay+eps)
                        elif method=='mape': thismismatch = abs(modely - datay[i]) / (datay[i]+eps)
                        elif method=='mad':  thismismatch = abs(modely - datay[i])
                        elif method=='mse':  thismismatch = (modely - datay[i])**2
                        else:
                            errormsg = 'autofit(): "method" not known; you entered "%s", but must be one of:\n' % method
                            errormsg += '"wape" = weighted absolute percentage error (default)\n'
                            errormsg += '"mape" = mean absolute percentage error\n'
                            errormsg += '"mad"  = mean absolute difference\n'
                            errormsg += '"mse"  = mean squared error'
                            raise OptimaException(errormsg)
                        allmismatches.append(thismismatch)
                        mismatch += thismismatch
                        
                        if doplot:
                            tmpdebugdata = (count, key, rowname, year, datay[i], modely, thismismatch, mismatch)
                            printv('#%i. Key="%s" pop="%s" year=%f datay=%f modely=%f thismis=%f totmis=%f' % tmpdebugdata, 4, verbose)
                            debugdata.append(tmpdebugdata)
                        
    
    if doplot:
        autofitresults['count'].append(len(autofitresults['count'])) #  Append new count
        autofitresults['mismatch'].append(mismatch) #  Append mismatch
        autofitresults['allmismatches'].append(array(allmismatches).flatten()) #  Append mismatch
        
        autofitfig.clear()
        nplots = len(set([d[1]+d[2] for d in debugdata]))+2 # 1 is the mismatch
        rows = ceil(sqrt(nplots))
        cols = rows-1 if rows*(rows-1)>=nplots else rows
        
        subplot(rows,cols,1)
        scatter(autofitresults['count'], autofitresults['mismatch'])
        xlabel('Count')
        ylabel('Mismatch')
        ylim((0,ylim()[1]))
        
        subplot(rows,cols,2)
        allmis = autofitresults['allmismatches'][-1] # Shorten
        bar(arange(len(allmis)), allmis)
        xlabel('Data point')
        ylabel('Mismatch')
        ylim((0,ylim()[1]))
        
        # Process data for plotting
        plotdata = odict()
        for count,key,rowname,year,datay,modely,thismismatch,mismatch in debugdata:
            if key not in plotdata: plotdata[key] = odict()
            if rowname not in plotdata[key]: 
                plotdata[key][rowname] = odict([('x',[]), ('datay',[]), ('modely',[])])
            plotdata[key][rowname]['x'].append(year)
            plotdata[key][rowname]['datay'].append(datay)
            plotdata[key][rowname]['modely'].append(modely)
        
        count = 0
        for key1,tmp1 in plotdata.items():
            for key2,tmp2 in tmp1.items():
                count += 1
                subplot(rows, cols, count+2)
                scatter(tmp2['x'], tmp2['datay'])
                plot(tmp2['x'], tmp2['modely'])
                ylabel(key1+' - '+key2)
                ylim((0,ylim()[1]))
        
        show()
        pause(0.001)
        
    printv('Current mismatch: %s' % array(mismatch), 4, verbose=verbose)
    return mismatch