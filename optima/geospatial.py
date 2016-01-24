"""
GEOSPATIAL

This file defines everything needed for the Python GUI for geospatial analysis.

Version: 2016jan23
"""

from optima import Project, Portfolio, loadobj, saveobj, odict, defaultobjectives
from PyQt4 import QtGui
from pylab import figure, close
global geoguiwindow
geoguiwindow = None

def geogui():
    '''
    Open the GUI for doing geospatial analysis.
    
    Version: 2016jan23
    '''
    global geoguiwindow, portfolio, projectslist, objectives, objectiveinputs
    portfolio = None
    projectslist = []
    objectives = defaultobjectives()
    
    ## Set parameters
    wid = 650.0
    hei = 550.0
    top = 20
    spacing = 40
    left = 20.
    projext = '.prj'
    portext = '.prt'
    
    ## Housekeeping
    fig = figure(); close(fig) # Open and close figure...dumb, no? Otherwise get "QWidget: Must construct a QApplication before a QPaintDevice"
    geoguiwindow = QtGui.QWidget() # Create panel widget
    geoguiwindow.setGeometry(100, 100, wid, hei)
    geoguiwindow.setWindowTitle('Optima geospatial analysis')
    projectslist = []
    
    ##############################################################################################################################
    ## Define functions
    ##############################################################################################################################

    
    def _loadproj():
        ''' Little helper function to load a project, since used more than once '''
        filepath = QtGui.QFileDialog.getOpenFileNames(caption='Choose project file', filter='*'+projext)
        project = None
        try: 
            project = loadobj(filepath, verbose=0)
        except: 
            print('Could not load file "%s"' % filepath)
            return None
        try: 
            assert type(project)==Project
            return project
        except: 
            print('File "%s" is not an Optima project file' % filepath)
            return None
        
        
    def makesheet():
        ''' Create a geospatial spreadsheet template based on a project file '''
        
        ## 1. Load a project file
        project = _loadproj()
            
        ## 2. Get destination filename
        spreadsheetpath = QtGui.QFileDialog.getSaveFileName(caption='Save geospatial spreadsheet file', filter='*.xlsx')
        
        ## 3. Extract data needed from project (population names, program names...)
        # ...
        
        ## 4. Generate and save spreadsheet
        # ...

        return None
        
    
    def makeproj():
        ''' Create a series of project files based on a seed file and a geospatial spreadsheet '''
        
        ## 1. Load a project file -- WARNING, could be combined with the above!
        project = _loadproj()
        
        ## 2. Load a spreadsheet file
        spreadsheetpath = QtGui.QFileDialog.getOpenFileNames(caption='Choose geospatial spreadsheet', filter='*.xlsx')
        
        ## 3. Get a destination folder
        destination = QtGui.QFileDialog.getExistingDirectory(caption='Choose output folder')
        
        ## 4. Read the spreadsheet
        # ...
        
        ## 5. Calibrate each project file according to the data entered for it in the spreadsheet
        # ...
        
        ## 6. Save each project file into the directory
        # ...
        
        return None


    def create():
        ''' Create a portfolio by selecting a list of projects; silently skip files that fail '''
        global projectslist
        projectslist = []
        projectpaths = []
        filepaths = QtGui.QFileDialog.getOpenFileNames(caption='Choose project files', filter='*'+projext)
        for filepath in filepaths:
            tmpproj = None
            try: tmpproj = loadobj(filepath, verbose=0)
            except: print('Could not load file "%s"; moving on...' % filepath)
            if tmpproj is not None: 
                try: 
                    assert type(tmpproj)==Project
                    projectslist.append(tmpproj)
                    projectpaths.append(filepath)
                    print('Project file "%s" loaded' % filepath)
                except: print('File "%s" is not an Optima project file; moving on...' % filepath)
        projectsbox.setText('\n'.join(projectpaths))
        portfolio = Portfolio()
        for project in projectslist: portfolio.addproject(project)
        return None
    
    def loadport():
        ''' Load an existing portfolio '''
        global portfolio
        filepath = QtGui.QFileDialog.getOpenFileName(caption='Choose portfolio file', filter='*'+portext)
        tmpport = None
        try: tmpport = loadobj(filepath, verbose=0)
        except: print('Could not load file "%s"' % filepath)
        if tmpport is not None: 
            try: 
                assert type(tmpport)==Portfolio
                portfolio = tmpport
                print('Portfolio file "%s" loaded' % filepath)
            except: print('File "%s" is not an Optima portfolio file' % filepath)
        projectsbox.setText('\n'.join([proj.name for proj in portfolio.projects.values()]))
        portfolio = Portfolio()
        for project in projectslist: portfolio.addproject(project)
        return None
    
    
    def rungeo():
        ''' Actually run geospatial analysis!!! '''
        global portfolio, objectives, objectiveinputs
        for key in objectives.keys():
            objectives[key] = eval(str(objectiveinputs[key].text())) # Get user-entered values
        portfolio.genBOCs(objectives)
        portfolio.plotBOCs(objectives)
        # ...
        return None
    
    
    def export():
        ''' Save the current portfolio to disk '''
        global portfolio
        if type(portfolio)!=Portfolio: print('Warning, must load portfolio first!')
        
        # 1. Extract data needed from portfolio
        # ...
        
        # 2. Generate spreadsheet according to David's template to store these data
        # ...
        
        # 3. Create a new file dialog to save this spreadsheet
        # ...
        return None
        

    def saveport():
        ''' Save the current portfolio '''
        global portfolio
        filepath = QtGui.QFileDialog.getSaveFileName(caption='Save portfolio file', filter='*'+portext)
        saveobj(filepath, portfolio)
        return None


    def closewindow(): 
        ''' Close the control panel '''
        global geoguiwindow
        geoguiwindow.close()
        return None
    
    
    ##############################################################################################################################
    ## Define buttons
    ##############################################################################################################################
    
    ## Define buttons
    buttons = odict()
    buttons['makesheet'] = QtGui.QPushButton('Make geospatial template from project', parent=geoguiwindow)
    buttons['makeproj']  = QtGui.QPushButton('Auto-generate projects template', parent=geoguiwindow)
    buttons['create']    = QtGui.QPushButton('Create portfolio from projects', parent=geoguiwindow)
    buttons['loadport']  = QtGui.QPushButton('Load existing portfolio', parent=geoguiwindow)
    buttons['rungeo']    = QtGui.QPushButton('Run geospatial analysis', parent=geoguiwindow)
    buttons['export']    = QtGui.QPushButton('Export results', parent=geoguiwindow)
    buttons['saveport']  = QtGui.QPushButton('Save portfolio', parent=geoguiwindow)
    buttons['close']     = QtGui.QPushButton('Close', parent=geoguiwindow)
    
    ## Define button functions
    actions = odict()
    actions['makesheet'] = makesheet
    actions['makeproj']  = makeproj
    actions['create']    = create
    actions['loadport']  = loadport
    actions['rungeo']    = rungeo
    actions['export']    = export
    actions['saveport']  = saveport
    actions['close']     = closewindow
    
    ## Set button locations
    spacer = 0
    for b,key in enumerate(buttons.keys()):
        if key=='rungeo': spacer = 200
        buttons[key].move(left, top+spacing*b+spacer)
    
    ## Define button functions
    for key in buttons.keys():
        buttons[key].clicked.connect(actions[key])
    
    
    
    ##############################################################################################################################
    ## Define other objects
    ##############################################################################################################################
    
    ## List of projects
    projectsbox = QtGui.QTextEdit(parent=geoguiwindow)
    projectsbox.move(300, 20)
    projectsbox.resize(wid-320, hei-40)
    projectsbox.setReadOnly(True)
    projectsbox.verticalScrollBar()
    
    ## Objectives
    objectivetext = odict()
    objectivetext['start']       = 'Start year:'
    objectivetext['end']         = 'End year:'
    objectivetext['budget']      = 'Total budget:'
    objectivetext['deathweight'] = 'Deaths weight:'
    objectivetext['inciweight']  = 'Infections weight:'
    
    objectivetextobjs = odict()
    for k,key in enumerate(objectivetext.keys()):
        objectivetextobjs[key] = QtGui.QLabel(parent=geoguiwindow)
        objectivetextobjs[key].setText(str(objectivetext[key]))
        objectivetextobjs[key].move(left+10, 205+k*30)
    
    objectiveinputs = odict()
    for k,key in enumerate(objectives.keys()):
        objectiveinputs[key] = QtGui.QLineEdit(parent=geoguiwindow)
        objectiveinputs[key].setText(str(objectives[key]))
        objectiveinputs[key].move(left+120, 200+k*30)
    

    geoguiwindow.show()