"""
CALIBRATION

Functions to perform calibration.
"""

from optima import dcp, perturb, Parameterset
from numpy import median
global panel # For manualfit GUI



def sensitivity(orig=None, ncopies=5, what='force', span=0.5, ind=0):
    ''' 
    Function to perturb the parameters to get "uncertainties".
    
    Inputs:
        orig = parset to perturb
        ncopies = number of perturbed copies of pars to produce
        what = which parameters to perturb
        span = how much to perturb
        ind = index of pars to start from
    Outputs:
        parset = perturbed parameter set with ncopies sets of pars
    
    Version: 2015dec29 by cliffk
    '''
    
    # Validate input
    if span>1 or span<0:
        print('WARNING: span argument must be a scalar in the interval [0,1], resetting...')
        span = median([0,1,span])
    if type(orig)!=Parameterset:
        raise Exception('First argument to sensitivity() must be a parameter set')
    
    # Copy things
    parset = dcp(orig) # Copy the original parameter set
    origpars = dcp(parset.pars[ind])
    parset.pars = []
    for n in range(ncopies):
        parset.pars.append(dcp(origpars))
    popkeys = origpars['popkeys']
    
    if what=='force':
        for n in range(ncopies):
            for key in popkeys:
                parset.pars[n]['force'][key] = perturb(n=1, span=span)[0] # perturb() returns array, so need to index -- WARNING, could make more efficient and remove loop
    else:
        raise Exception('Sorry, only "force" is implemented currently')
    
    return parset








def manualfit(project=None, name='default', ind=0):
    ''' 
    Create a GUI for doing manual fitting via the backend. Opens up three windows: 
    results, results selection, and edit boxes.
    
    Current version only allows the user to modify force-of-infection, 
    
    Version: 1.0 (2015dec29) by cliffk
    '''
    global panel
    
    ## Set up imports for plotting...need Qt since matplotlib doesn't support edit boxes, grr!
    from PyQt4 import QtGui
    from pylab import figure, close
    fig = figure(); close(fig) # Open and close figure...dumb, no?
    
    ## Get the list of parameters that can be fitted
    pars = project.parsets[name].pars[0]
    keylist = []
    namelist = []
    typelist = [] # Valid types are meta, pop, exp
    for key in pars.keys():
        if hasattr(pars[key],'manual'): # Don't worry if it doesn't work, not everything in pars is actually a parameter
            if pars[key].manual is not '':
                keylist.append(key) # e.g. "initprev"
                namelist.append(pars[key].name) # e.g. "HIV prevalence"
                typelist.append(pars[key].manual) # e.g. 'pop'
    nkeys = len(keylist) # Number of keys...note, this expands due to different populations etc.
    
    ## Convert to the full list of parameters to be fitted
    fulllabellist = [] # e.g. "Initial HIV prevalence -- FSW"
    fullkeylist = [] # e.g. "initprev"
    fullsubkeylist = [] # e.g. "fsw"
    fulltypelist = [] # e.g. "pop"
    fullvallist = [] # e.g. 0.3
    for k in range(nkeys):
        key = keylist[k]
        if typelist[k]=='meta':
            fullkeylist.append(key)
            fullsubkeylist.append(None)
            fulltypelist.append(typelist[k])
            fullvallist.append(pars[key].m)
            fulllabellist.append(namelist[k] + '(meta)')
        elif typelist[k]=='pop' or typelist[k]=='pship':
            for subkey in pars[key].y.keys():
                fullkeylist.append(key)
                fullsubkeylist.append(subkey)
                fulltypelist.append(typelist[k])
                fullvallist.append(pars[key].y[subkey])
                fulllabellist.append(namelist[k] + ' -- ' + str(subkey))
    nfull = len(fulllabellist) # The total number of boxes needed
    
    
    ## Define update step
    def update(val):
        for box in boxes:
            print('I am box and my value is %s' % (box.text()))
    
    ## Create control panel
    boxes = []
    panel = QtGui.QWidget() # Create panel widget
    panel.setGeometry(300, 300, 250, 150)
    for i in range(3):
        boxes.append(QtGui.QLineEdit(parent = panel)) # Actually create the text edit box
        boxes[-1].move(50, 50*(i+1))
        boxes[-1].textChanged.connect(update)
    panel.show()
















def autofit(orig=None, what='force', ind=0):
    ''' 
    Function to automatically fit the parameters to get "uncertainties".
    
    Inputs:
        orig = parset to perturb
        what = which parameters to perturb
        ind = index of pars to start from
    Outputs:
        parset = auto-fitted parameter set
    
    Version: 1.0 (2015dec29) by cliffk
    '''
    
#    # Validate input
#    if type(orig)!=Parameterset:
#        raise Exception('First argument to sensitivity() must be a parameter set')
#    
#    # Copy things
#    parset = dcp(orig) # Copy the original parameter set
#    origpars = dcp(parset.pars[ind])
#    parset.pars = [dcp(origpars)]
#    popkeys = origpars['popkeys']
#    
#    if what=='force':
#        for key in popkeys:
#            parset.pars[n]['force'][key] = perturb(n=1, span=span)[0] # perturb() returns array, so need to index -- WARNING, could make more efficient and remove loop
#    else:
#        raise Exception('Sorry, only "force" is implemented currently')
#    
#    return parset