"""
GEOSPATIAL

This file defines everything needed for the Python GUI for geospatial analysis.

Version: 2016jan29
"""

global geoguiwindow
geoguiwindow = None

def geogui():
    '''
    Open the GUI for doing geospatial analysis.
    
    Version: 2016jan23
    '''
    from optima import Project, Portfolio, loadobj, saveobj, odict, defaultobjectives, dcp
    from PyQt4 import QtGui
    from pylab import figure, close
    global geoguiwindow, guiportfolio, objectives, objectiveinputs, projectslistbox, projectinfobox
    guiportfolio = None
    objectives = defaultobjectives()
    objectives['budget'] = 0.0 # Reset
    
    ## Global options
    budgetfactor = 1e6 # Conversion between screen and internal
    
    ## Set parameters
    wid = 1200.0
    hei = 600.0
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
    
    
    
    
    
    ##############################################################################################################################
    ## Define functions
    ##############################################################################################################################

    
    def _loadproj():
        ''' Helper function to load a project, since used more than once '''
        filepath = QtGui.QFileDialog.getOpenFileNames(caption='Choose project file', filter='*'+projext)
        project = None
        if filepath:
            try: project = loadobj(filepath, verbose=0)
            except: print('Could not load file "%s"' % filepath)
            if type(project)==Project: return project
            else: print('File "%s" is not an Optima project file' % filepath)
        return None
    
    
    def resetbudget():
        ''' Replace current displayed budget with default from portfolio '''
        global guiportfolio, objectiveinputs
        totalbudget = 0
        for project in guiportfolio.projects.values():
            totalbudget += sum(project.progsets[0].getdefaultbudget().values())
        objectiveinputs['budget'].setText(str(totalbudget/budgetfactor))
        return None
    
    def warning(message):
        global geoguiwindow
        QtGui.QMessageBox.warning(geoguiwindow, 'Message', message)
        
        
    def makesheet():
        ''' Create a geospatial spreadsheet template based on a project file '''
        warning("Sorry, this feature has not been implemented.")
        
        ## 1. Load a project file
#        project = _loadproj()
            
        ## 2. Get destination filename
#        spreadsheetpath = QtGui.QFileDialog.getSaveFileName(caption='Save geospatial spreadsheet file', filter='*.xlsx')
        
        ## 3. Extract data needed from project (population names, program names...)
        # ...
        
        ## 4. Generate and save spreadsheet
        # ...

        return None
        
    
    def makeproj():
        ''' Create a series of project files based on a seed file and a geospatial spreadsheet '''
        warning("Sorry, this feature has not been implemented.")
        
        ## 1. Load a project file -- WARNING, could be combined with the above!
#        project = _loadproj()
        
        ## 2. Load a spreadsheet file
#        spreadsheetpath = QtGui.QFileDialog.getOpenFileNames(caption='Choose geospatial spreadsheet', filter='*.xlsx')
        
        ## 3. Get a destination folder
#        destination = QtGui.QFileDialog.getExistingDirectory(caption='Choose output folder')
        
        ## 4. Read the spreadsheet
        # ...
        
        ## 5. Calibrate each project file according to the data entered for it in the spreadsheet
        # ...
        
        ## 6. Save each project file into the directory
        # ...
        
        return None


    def create(doadd=False):
        ''' Create a portfolio by selecting a list of projects; silently skip files that fail '''
        global guiportfolio, projectslistbox, objectives, objectiveinputs
        projectpaths = []
        projectslist = []
        if guiportfolio is None: 
            guiportfolio = Portfolio()
        if not doadd:
            guiportfolio = Portfolio()
            projectslistbox.clear()
        filepaths = QtGui.QFileDialog.getOpenFileNames(caption='Choose project files', filter='*'+projext)
        if type(filepaths)==str: filepaths = [filepaths] # Convert to list
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
        projectslistbox.addItems(projectpaths)
        guiportfolio.addprojects(projectslist)
        resetbudget() # And reset the budget
        return None
    
    
    def addproj():
        ''' Add a project -- same as creating a portfolio except don't overwrite '''
        global guiportfolio, objectives
        create(doadd=True)
        resetbudget() # And reset the budget
        return None
    
    
    def loadport():
        ''' Load an existing portfolio '''
        global guiportfolio, projectslistbox
        filepath = QtGui.QFileDialog.getOpenFileName(caption='Choose portfolio file', filter='*'+portext)
        tmpport = None
        if filepath:
            try: tmpport = loadobj(filepath, verbose=0)
            except: print('Could not load file "%s"' % filepath)
            if tmpport is not None: 
                if type(tmpport)==Portfolio:
                    guiportfolio = tmpport
                    projectslistbox.clear()
                    projectslistbox.addItems([proj.name for proj in guiportfolio.projects.values()])
                    print('Portfolio file "%s" loaded' % filepath)
                else: print('File "%s" is not an Optima portfolio file' % filepath)
        resetbudget() # And reset the budget
        return None
    
    
    def rungeo():
        ''' Actually run geospatial analysis!!! '''
        global guiportfolio, objectives, objectiveinputs
        for key in objectiveinputs.keys():
            objectives[key] = eval(str(objectiveinputs[key].text())) # Get user-entered values
        objectives['budget'] *= budgetfactor # Convert back to internal representation
        BOCobjectives = dcp(objectives)
        guiportfolio.genBOCs(BOCobjectives, maxtime=5) # WARNING temp time
        guiportfolio.fullGA(objectives, doplotBOCs=True, budgetratio = guiportfolio.getdefaultbudgets(), maxtime=5) # WARNING temp time
        return None
    
    
    
    def export():
        ''' Save the current results to Excel file '''
        global guiportfolio
        if type(guiportfolio)!=Portfolio: print('Warning, must load portfolio first!')
        
        from xlsxwriter import Workbook
        
        # 1. Extract data needed from portfolio
        try:
            outstr = guiportfolio.outputstring
        except:
            warning('Warning, it does not seem that geospatial analysis has been run for this portfolio!')
            return None
        
        # 2. Create a new file dialog to save this spreadsheet
        filepath = QtGui.QFileDialog.getSaveFileName(caption='Save geospatial analysis results file', filter='*.xlsx')
        
        # 2. Generate spreadsheet according to David's template to store these data
        workbook = Workbook(filepath)
        worksheet = workbook.add_worksheet()
        
        # Convert from a string to a 2D array
        outlist = []
        for line in outstr.split('\n'):
            outlist.append([])
            for cell in line.split('\t'):
                outlist[-1].append(cell)
            
        # Iterate over the data and write it out row by row.
        row, col = 0, 0
        for row in range(len(outlist)):
            for col in range(len(outlist[row])):
                worksheet.write(row, col, outlist[row][col])
        workbook.close()
        return None
        

    def saveport():
        ''' Save the current portfolio '''
        global guiportfolio
        filepath = QtGui.QFileDialog.getSaveFileName(caption='Save portfolio file', filter='*'+portext)
        saveobj(filepath, guiportfolio)
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
    buttons['makesheet'] = QtGui.QPushButton('Make geospatial spreadsheet from project', parent=geoguiwindow)
    buttons['makeproj']  = QtGui.QPushButton('Auto-generate projects from spreadsheet', parent=geoguiwindow)
    buttons['create']    = QtGui.QPushButton('Create portfolio from projects', parent=geoguiwindow)
    buttons['add']       = QtGui.QPushButton('Add projects to portfolio', parent=geoguiwindow)
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
    actions['add']       = addproj
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
    
    def updateprojectinfo():
        global guiportfolio, projectslistbox, projectinfobox
        ind = projectslistbox.currentRow()
        project = guiportfolio.projects[ind]
        projectinfobox.setText(repr(project))
        return None
    
    def removeproject():
        global projectslistbox, projectinfobox, guiportfolio
        ind = projectslistbox.currentRow()
        guiportfolio.projects.pop(guiportfolio.projects.keys()[ind]) # Remove from portfolio
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
    objectivetext['budget']      = 'Total budget ($m):'
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
        objectiveinputs[key].setText(str(objectives[key]))
        objectiveinputs[key].move(left+120, 230+k*30)
    objectiveinputs['budget'].setText(str(objectives['budget']/budgetfactor)) # So right units
    

    geoguiwindow.show()