## Imports and globals...need Qt since matplotlib doesn't support edit boxes, grr!
from optima import dcp, printv, sigfig
from pylab import figure, close, floor, ion
from PyQt4 import QtGui
import gui # Need low-level functions so need to import directly
global panel, panelfig, plotfig, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist  # For manualfit GUI
if 1:  panel, panelfig, plotfig, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist = [None]*12

def manualgui(project=None, name='default', ind=0, verbose=4):
    ''' 
    Create a GUI for doing manual fitting via the backend. Opens up three windows: 
    results, results selection, and edit boxes.
    
    Current version only allows the user to modify force-of-infection, 
    
    Version: 1.0 (2015dec29) by cliffk
    '''
    
    ## Random housekeeping
    global panel, panelfig, plotfig, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
    fig = figure(); close(fig) # Open and close figure...dumb, no?
    ion() # We really need this here!
    nsigfigs = 3
    
    ## Initialize lists that do not initialize themselves
    boxes = []
    texts = []
    keylist = []
    namelist = []
    typelist = [] # Valid types are meta, pop, exp
    
    ## Get the list of parameters that can be fitted
    parset = dcp(project.parsets[name])
    tmppars = parset.pars[0]
    origpars = dcp(tmppars)

    for key in tmppars.keys():
        if hasattr(tmppars[key],'manual'): # Don't worry if it doesn't work, not everything in tmppars is actually a parameter
            if tmppars[key].manual is not '':
                keylist.append(key) # e.g. "initprev"
                namelist.append(tmppars[key].name) # e.g. "HIV prevalence"
                typelist.append(tmppars[key].manual) # e.g. 'pop'
    nkeys = len(keylist) # Number of keys...note, this expands due to different populations etc.
    
    ## Convert to the full list of parameters to be fitted
    def populatelists():
        global tmppars, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
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
                fullvallist.append(tmppars[key].m)
                fulllabellist.append(namelist[k] + ' -- meta')
            elif typelist[k]=='pop' or typelist[k]=='pship':
                for subkey in tmppars[key].y.keys():
                    fullkeylist.append(key)
                    fullsubkeylist.append(subkey)
                    fulltypelist.append(typelist[k])
                    fullvallist.append(tmppars[key].y[subkey])
                    fulllabellist.append(namelist[k] + ' -- ' + str(subkey))
            elif typelist[k]=='exp':
                for subkey in tmppars[key].p.keys():
                    fullkeylist.append(key)
                    fullsubkeylist.append(subkey)
                    fulltypelist.append(typelist[k])
                    fullvallist.append(tmppars[key].p[subkey][0])
                    fulllabellist.append(namelist[k] + ' -- ' + str(subkey))
            else:
                print('Parameter type "%s" not implemented!' % typelist[k])
    
    populatelists()
    nfull = len(fulllabellist) # The total number of boxes needed
    results = project.runsim(name)
    gui.pygui(results)
    
    
    
    def closewindows():
        ''' Close all three open windows '''
        gui.closegui()
        panel.close()
    
    
    ## Define update step
    def update():
        ''' Update GUI with new results '''
        global results, tmppars, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
        
        ## Loop over all parameters and update them
        for b,box in enumerate(boxes):
            if fulltypelist[b]=='meta': # Metaparameters
                key = fullkeylist[b]
                tmppars[key].m = eval(str(box.text()))
                printv('%s.m = %s' % (key, box.text()), 4, verbose=verbose)
            elif fulltypelist[b]=='pop' or fulltypelist[b]=='pship': # Populations or partnerships
                key = fullkeylist[b]
                subkey = fullsubkeylist[b]
                tmppars[key].y[subkey] = eval(str(box.text()))
                printv('%s.y[%s] = %s' % (key, subkey, box.text()), 4, verbose=verbose)
            elif fulltypelist[b]=='exp': # Population growth
                key = fullkeylist[b]
                subkey = fullsubkeylist[b]
                tmppars[key].p[subkey][0] = eval(str(box.text()))
                printv('%s.p[%s] = %s' % (key, subkey, box.text()), 4, verbose=verbose)
            else:
                print('Parameter type "%s" not implemented!' % fulltypelist[b])
        
        simparslist = parset.interp()
        results = project.runsim(simpars=simparslist)
        gui.update(tmpresults=results)
        
    
    ## Keep the current parameters in the project; otherwise discard
    def keeppars():
        ''' Little function to reset origpars and update the project '''
        global origpars, tmppars, parset
        origpars = dcp(tmppars)
        parset.pars[0] = tmppars
        project.parsets[name].pars[0] = tmppars
        print('Parameters kept')
        return None
    
    
    def resetpars():
        ''' Reset the parameters to the last saved version '''
        global origpars, tmppars, parset
        tmppars = dcp(origpars)
        parset.pars[0] = tmppars
        populatelists()
        for i in range(nfull): boxes[i].setText(sigfig(fullvallist[i], sigfigs=nsigfigs))
        simparslist = parset.interp()
        results = project.runsim(simpars=simparslist)
        gui.update(tmpresults=results)
        return None
    

    ## Set up GUI
    leftmargin = 10
    rowheight = 25
    colwidth = 450
    ncols = 2
    panelwidth = colwidth*ncols
    panelheight = rowheight*(nfull/ncols+2)+50
    buttonheight = panelheight-rowheight*1.5
    buttonoffset = (panelwidth-400)/2
    boxoffset = 250+leftmargin
    
    panel = QtGui.QWidget() # Create panel widget
    panel.setGeometry(100, 100, panelwidth, panelheight)
    for i in range(nfull):
        row = (i % floor((nfull+1)/2))+1
        col = floor(2*i/nfull)
        
        texts.append(QtGui.QLabel(parent=panel))
        texts[-1].setText(fulllabellist[i])
        texts[-1].move(leftmargin+colwidth*col, rowheight*row)
        
        boxes.append(QtGui.QLineEdit(parent = panel)) # Actually create the text edit box
        boxes[-1].move(boxoffset+colwidth*col, rowheight*row)
        boxes[-1].setText(sigfig(fullvallist[i], sigfigs=nsigfigs))
        boxes[-1].returnPressed.connect(update)
    
    keepbutton  = QtGui.QPushButton('Keep', parent=panel)
    resetbutton = QtGui.QPushButton('Reset', parent=panel)
    closebutton = QtGui.QPushButton('Close', parent=panel)
    
    keepbutton.move(0+buttonoffset, buttonheight)
    resetbutton.move(200+buttonoffset, buttonheight)
    closebutton.move(400+buttonoffset, buttonheight)
    
    keepbutton.clicked.connect(keeppars)
    resetbutton.clicked.connect(resetpars)
    closebutton.clicked.connect(closewindows)
    panel.show()