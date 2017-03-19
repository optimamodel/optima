"""
GEOSPATIAL

This file defines everything needed for the Python GUI for geospatial analysis.

Version: 2016nov03
"""

from optima import Project, Portfolio, loadproj, loadobj, saveobj, odict, defaultobjectives, dcp, OptimaException, makegeospreadsheet, makegeoprojects
from PyQt4 import QtGui
from pylab import figure, close
from time import time


global geoguiwindow, globalportfolio, globalobjectives
if 1:  geoguiwindow, globalportfolio, globalobjectives = [None]*3

    
    
## Global options
budgetfactor = 1e6 # Conversion between screen and internal
prjext = '.prj'
prtext = '.prt'



##############################################################################################################################
## Define functions
##############################################################################################################################

def resetbudget():
    ''' Replace current displayed budget with default from portfolio '''
    global globalportfolio, objectiveinputs
    totalbudget = 0
    for project in globalportfolio.projects.values():
        totalbudget += sum(project.progsets[0].getdefaultbudget().values())
    objectiveinputs['budget'].setText(str(totalbudget/budgetfactor))
    return None


def warning(message, usegui=True):
    ''' usegui kwarg is so this can be used in a GUI and non-GUI context '''
    global geoguiwindow
    if usegui:
        QtGui.QMessageBox.warning(geoguiwindow, 'Message', message)
    else:
        print(message)
    
    
    
def gui_loadproj():
    ''' Helper function to load a project, since used more than once '''
    filepath = QtGui.QFileDialog.getOpenFileName(caption='Choose project file', filter='*'+prjext)
    project = None
    if filepath:
        try: project = loadproj(filepath, verbose=0)
        except Exception as E: print('Could not load file "%s": "%s"' % (filepath, E.message))
        if type(project)==Project: return project
        else: print('File "%s" is not an Optima project file' % filepath)
    else:
        print('No filepath provided')
    return project
    
    
def gui_makesheet():
    ''' Create a geospatial spreadsheet template based on a project file '''
    
    ## 1. Load a project file
    project = gui_loadproj() # No, it's a project path, load it
    if project is None: 
        raise OptimaException('No project loaded.')
    
    try:    results = project.parsets[-1].getresults()
    except: results = project.runsim(name=project.parsets[-1].name)
    
    copies, ok = QtGui.QInputDialog.getText(geoguiwindow, 'GA Spreadsheet Parameter', 'How many variants of the chosen project do you want?')
    try: copies = int(copies)
    except: raise OptimaException('Input (number of project copies) cannot be converted into an integer.')
    
    refyear, ok = QtGui.QInputDialog.getText(geoguiwindow, 'GA Spreadsheet Parameter', 'Select a reference year for which you have district data.')
    try: refyear = int(refyear)
    except: raise OptimaException('Input (reference year) cannot be converted into an integer.')
    if not refyear in [int(x) for x in results.tvec]:
        raise OptimaException("Input not within range of years used by aggregate project's last stored calibration.")

    ## 2. Get destination filename
    spreadsheetpath = QtGui.QFileDialog.getSaveFileName(caption='Save geospatial spreadsheet file', filter='*.xlsx')
    
    # 4. Generate and save spreadsheet
    try:
        makegeospreadsheet(project=project, spreadsheetpath=spreadsheetpath, copies=copies, refyear=refyear, verbose=2)
        warning('Multi-project template saved to "%s".' % spreadsheetpath)
    except:
        warning('Error: Template not saved due to a workbook error!')

    return None
    
    
def gui_makeproj():
    ''' Create a series of project files based on a seed file and a geospatial spreadsheet '''
    project = gui_loadproj()
    spreadsheetpath = QtGui.QFileDialog.getOpenFileName(caption='Choose geospatial spreadsheet', filter='*.xlsx')
    destination = QtGui.QFileDialog.getExistingDirectory(caption='Choose output folder')
    makegeoprojects(project=project, spreadsheetpath=spreadsheetpath, destination=destination)
    warning('Created projects from spreadsheet')
    return None


def gui_create(filepaths=None, portfolio=None, doadd=False):
    ''' Create a portfolio by selecting a list of projects; silently skip files that fail '''
    global globalportfolio, projectslistbox, objectiveinputs
    
    projectpaths = []
    projectslist = []
    if globalportfolio is None: 
        globalportfolio = Portfolio()
    if not doadd:
        globalportfolio = Portfolio()
        projectslistbox.clear()
    if doadd and portfolio != None:
        globalportfolio = portfolio
    filepaths = QtGui.QFileDialog.getOpenFileNames(caption='Choose project files', filter='*'+prjext)
    if filepaths:
        if type(filepaths)==str: filepaths = [filepaths] # Convert to list
        for filepath in filepaths:
            tmpproj = None
            try: tmpproj = loadproj(filepath, verbose=0)
            except: print('Could not load file "%s"; moving on...' % filepath)
            if tmpproj is not None: 
                if type(tmpproj)==Project:
                    projectslist.append(tmpproj)
                    projectpaths.append(filepath)
                    print('Project file "%s" loaded' % filepath)
                else: print('File "%s" is not an Optima project file; moving on...' % filepath)
        projectslistbox.addItems(projectpaths)
        globalportfolio.addprojects(projectslist)
        resetbudget() # And reset the budget
    return None


def gui_addproj(portfolio=None, filepaths=None):
    ''' Add a project -- same as creating a portfolio except don't overwrite '''
    p = gui_create(filepaths=filepaths, doadd=True, portfolio=portfolio)
    resetbudget() # And reset the budget
    return p


def gui_loadport(filepath=None):
    ''' Load an existing portfolio '''
    global globalportfolio, projectslistbox
    filepath = QtGui.QFileDialog.getOpenFileName(caption='Choose portfolio file', filter='*'+prtext)
    tmpport = None
    if filepath:
        try: tmpport = loadobj(filepath, verbose=0)
        except Exception as E: 
            warning('Could not load file "%s" because "%s"' % (filepath, E.message))
            return None
        if tmpport is not None: 
            if type(tmpport)==Portfolio:
                globalportfolio = tmpport
                projectslistbox.clear()
                projectslistbox.addItems([proj.name for proj in globalportfolio.projects.values()])
                print('Portfolio file "%s" loaded' % filepath)
            else: print('File "%s" is not an Optima portfolio file' % filepath)
    else:
        warning('File path not provided. Portfolio not loaded.')
    resetbudget() # And reset the budget
    return None


def gui_rungeo(portfolio=None, objectives=None, maxtime=30, mc=0, batch=True, verbose=2, die=False, strict=True):
    ''' Actually run geospatial analysis!!! '''
    global globalportfolio, globalobjectives, objectiveinputs
    starttime = time()
    if portfolio is not None:
        globalportfolio = portfolio
    if objectives is not None:
        globalobjectives = objectives
    if globalobjectives is None:
        globalobjectives = defaultobjectives()
        globalobjectives['budget'] = 0.0 # Reset
    for key in objectiveinputs.keys():
        globalobjectives[key] = eval(str(objectiveinputs[key].text())) # Get user-entered values
    globalobjectives['budget'] *= budgetfactor # Convert back to internal representation
    BOCobjectives = dcp(globalobjectives)
    try:
        globalportfolio.genBOCs(objectives=BOCobjectives, maxtime=maxtime, mc=mc)
        globalportfolio.runGA(objectives=globalobjectives, maxtime=maxtime, reoptimize=True, mc=mc, batch=batch, verbose=verbose, die=die, strict=strict)
    except Exception as E:
        warning('Geospatial analysis failed: %s' % E.__repr__())
    warning('Geospatial analysis finished running; total time: %0.0f s' % (time() - starttime))
    return None
    

def gui_plotgeo():
    ''' Actually plot geospatial analysis!!! '''
    global globalportfolio
    if globalportfolio is None: 
        warning('Please load a portfolio first')
        return None
    globalportfolio.plotBOCs(deriv=False)
    return None


def gui_export(portfolio=None, filepath=None):
    ''' Save the current results to Excel file '''
    global globalportfolio
    
    if portfolio is not None:
        globalportfolio = portfolio
        if filepath is None:
            filepath = portfolio.name+'.prt'
    if type(globalportfolio)!=Portfolio: warning('Warning, must load portfolio first!')
    
    # 2. Create a new file dialog to save this spreadsheet
    filepath = QtGui.QFileDialog.getSaveFileName(caption='Save geospatial analysis results file', filter='*.xlsx')
    
    # 3. Generate spreadsheet according to David's template to store these data
    if filepath:
        try:
            globalportfolio.export(filename=filepath)
        except Exception as E:
            warning('Results export failed: %s' % E.__repr__())
        warning('Results saved to "%s".' % filepath)
    else:
        warning('Filepath not supplied: %s' % filepath)
    
    return None
    

def gui_saveport(portfolio = None, filepath = None):
    ''' Save the current portfolio '''
    global globalportfolio
    if portfolio != None:
        globalportfolio = portfolio
    filepath = QtGui.QFileDialog.getSaveFileName(caption='Save portfolio file', filter='*'+prtext)
    saveobj(filepath, globalportfolio)
    return None


def closewindow(): 
    ''' Close the control panel '''
    global geoguiwindow
    geoguiwindow.close()
    return None
    

def geogui():
    '''
    Open the GUI for doing geospatial analysis.
    
    Version: 2016jan23
    '''
    global geoguiwindow, globalportfolio, globalobjectives, objectiveinputs, projectslistbox, projectinfobox
    globalportfolio = None
    if globalobjectives is None:
        globalobjectives = defaultobjectives()
        globalobjectives['budget'] = 0.0 # Reset
    
    ## Set parameters
    wid = 1200.0
    hei = 600.0
    top = 20
    spacing = 40
    left = 20.
    
    ## Housekeeping
    fig = figure(); close(fig) # Open and close figure...dumb, no? Otherwise get "QWidget: Must construct a QApplication before a QPaintDevice"
    geoguiwindow = QtGui.QWidget() # Create panel widget
    geoguiwindow.setGeometry(100, 100, wid, hei)
    geoguiwindow.setWindowTitle('Optima geospatial analysis')
    
    ##############################################################################################################################
    ## Define buttons
    ##############################################################################################################################
    
    ## Define buttons
    buttons = odict()
    buttons['makesheet'] = QtGui.QPushButton('Make geospatial spreadsheet from project', parent=geoguiwindow)
    buttons['makeproj']  = QtGui.QPushButton('Auto-generate projects from spreadsheet', parent=geoguiwindow)
    buttons['create']    = QtGui.QPushButton('Create portfolio from projects', parent=geoguiwindow)
    buttons['add']       = QtGui.QPushButton('Add projects to portfolio', parent=geoguiwindow)
    buttons['loadport']  = QtGui.QPushButton('Load existing portfolio', parent=geoguiwindow)
    buttons['rungeo']    = QtGui.QPushButton('Run geospatial analysis', parent=geoguiwindow)
    buttons['plotgeo']   = QtGui.QPushButton('Plot geospatial results', parent=geoguiwindow)
    buttons['export']    = QtGui.QPushButton('Export results', parent=geoguiwindow)
    buttons['saveport']  = QtGui.QPushButton('Save portfolio', parent=geoguiwindow)
    buttons['close']     = QtGui.QPushButton('Close', parent=geoguiwindow)
    
    ## Define button functions
    actions = odict()
    actions['makesheet'] = gui_makesheet
    actions['makeproj']  = gui_makeproj
    actions['create']    = gui_create
    actions['add']       = gui_addproj
    actions['loadport']  = gui_loadport
    actions['rungeo']    = gui_rungeo
    actions['plotgeo']   = gui_plotgeo
    actions['export']    = gui_export
    actions['saveport']  = gui_saveport
    actions['close']     = closewindow
    
    ## Set button locations
    spacer = 0
    for b,key in enumerate(buttons.keys()):
        if key=='rungeo': spacer = 170
        buttons[key].move(left, top+spacing*b+spacer)
    
    ## Define button functions
    for key in buttons.keys():
        buttons[key].clicked.connect(actions[key])
    
    
    
    ##############################################################################################################################
    ## Define other objects
    ##############################################################################################################################
    
    def updateprojectinfo():
        global globalportfolio, projectslistbox, projectinfobox
        ind = projectslistbox.currentRow()
        project = globalportfolio.projects[ind]
        projectinfobox.setText(repr(project))
        return None
    
    def removeproject():
        global projectslistbox, projectinfobox, globalportfolio
        ind = projectslistbox.currentRow()
        globalportfolio.projects.pop(globalportfolio.projects.keys()[ind]) # Remove from portfolio
        projectslistbox.takeItem(ind) # Remove from list
        return None
        
    
    ## List of projects
    projectslistlabel = QtGui.QLabel(parent=geoguiwindow)
    projectslistlabel.setText('Projects in this portfolio:')
    projectslistbox = QtGui.QListWidget(parent=geoguiwindow)
    projectslistbox.verticalScrollBar()
    projectslistbox.currentItemChanged.connect(updateprojectinfo)
    buttons['remove'] = QtGui.QPushButton('Remove selected project from portfolio', parent=geoguiwindow)
    buttons['remove'].clicked.connect(removeproject)
    projectslistlabel.move(330,20)
    projectslistbox.move(330, 40)
    buttons['remove'].move(330, hei-40)
    projectslistbox.resize(300, hei-100)
    
    
    ## Project info
    projectsinfolabel = QtGui.QLabel(parent=geoguiwindow)
    projectsinfolabel.setText('Information about the selected project:')
    projectinfobox = QtGui.QTextEdit(parent=geoguiwindow)
    projectinfobox.setReadOnly(True)
    projectinfobox.verticalScrollBar()
    projectsinfolabel.move(640,20)
    projectinfobox.move(640, 40)
    projectinfobox.resize(530, hei-100)
    
    ## Objectives
    objectivetext = odict()
    objectivetext['start']       = 'Start year:'
    objectivetext['end']         = 'End year:'
    objectivetext['budget']      = 'Total budget (mil.):'
    objectivetext['deathweight'] = 'Deaths weight:'
    objectivetext['inciweight']  = 'Infections weight:'
    
    objectivetextobjs = odict()
    for k,key in enumerate(objectivetext.keys()):
        objectivetextobjs[key] = QtGui.QLabel(parent=geoguiwindow)
        objectivetextobjs[key].setText(str(objectivetext[key]))
        objectivetextobjs[key].move(left+10, 235+k*30)
    
    objectiveinputs = odict()
    for k,key in enumerate(objectivetext.keys()):
        objectiveinputs[key] = QtGui.QLineEdit(parent=geoguiwindow)
        objectiveinputs[key].setText(str(globalobjectives[key]))
        objectiveinputs[key].move(left+120, 230+k*30)
    objectiveinputs['budget'].setText(str(globalobjectives['budget']/budgetfactor)) # So right units
    

    geoguiwindow.show()