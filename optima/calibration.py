"""
CALIBRATION

Functions to perform calibration.
"""

from optima import dcp, perturb, Parameterset
from numpy import median



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
    
    
    
    
    
    
    
    import numpy as np
    from matplotlib import use
    use("Qt4Agg") # This program works with Qt only
    import pylab as pl
    fig, ax1 = pl.subplots()
    
    t = np.linspace(0, 10, 200)
    
    line, = ax1.plot(t, np.sin(t))
    
    ### control panel ###
    from PyQt4 import QtGui
    from PyQt4.QtCore import Qt
    
    def update():
        freq = float(textbox.text())
        y = np.sin(2*np.pi*freq*t)
        line.set_data(t, y)
        fig.canvas.draw_idle()
    
    root = fig.canvas.manager.window
    panel = QtGui.QWidget()
    hbox = QtGui.QHBoxLayout(panel)
    textbox = QtGui.QLineEdit(parent = panel)
    textbox.textChanged.connect(update)
    hbox.addWidget(textbox)
    panel.setLayout(hbox)
    
    dock = QtGui.QDockWidget("control", root)
    root.addDockWidget(Qt.BottomDockWidgetArea, dock)
    dock.setWidget(panel)
    ######################
    
    pl.show()


















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