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
    from optima import Project, Portfolio, loadobj, saveobj, odict, defaultobjectives, dcp, OptimaException
    from PyQt4 import QtGui
    from pylab import figure, close
    from time import time
    global geoguiwindow, guiportfolio, guiobjectives, objectiveinputs, projectslistbox, projectinfobox
    guiportfolio = None
    guiobjectives = defaultobjectives()
    guiobjectives['budget'] = 0.0 # Reset
    
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
        filepath = QtGui.QFileDialog.getOpenFileName(caption='Choose project file', filter='*'+projext)
        project = None
        if filepath:
            try: project = loadobj(filepath, verbose=0)
            except Exception as E: print('Could not load file "%s": "%s"' % (filepath, E.message))
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
        
        
    # WARNING: HARDCODING ZEROTH PROGSET AND PARSET THROUGHOUT.
    def makesheet():
        ''' Create a geospatial spreadsheet template based on a project file '''      
        
        ## 1. Load a project file
        project = _loadproj()
        
        copies, ok = QtGui.QInputDialog.getText(geoguiwindow, 'GA Spreadsheet Parameter', 'How many variants of the chosen project do you want?')
        try: copies = int(copies)
        except: raise OptimaException('Input is not a recognised integer.')
        colwidth = 20
            
        ## 2. Get destination filename
        spreadsheetpath = QtGui.QFileDialog.getSaveFileName(caption='Save geospatial spreadsheet file', filter='*.xlsx')
        
        from xlsxwriter import Workbook        
        
        ## 3. Extract data needed from project (population names, program names...)
        if spreadsheetpath:
            workbook = Workbook(spreadsheetpath)
            wsprev = workbook.add_worksheet('Population prevalence')
            wspopsize = workbook.add_worksheet('Population sizes')
            wsalloc = workbook.add_worksheet('Program allocations')
            
            # Start with pop data.
            maxcol = 0
            row, col = 0, 0
            for row in xrange(copies+1):
                if row != 0:
                    wsprev.write(row, col, '%s - District %i' % (project.name, row))
                    wspopsize.write(row, col, '%s - District %i' % (project.name, row))
                for popname in project.parsets[0].popkeys:
                    col += 1
                    if row == 0:
                        wsprev.write(row, col, popname)
                        wspopsize.write(row, col, popname)
                    else:
                        pass
#                        wsprev.write(row, col, project.parsets[0].pars[0]['initprev'].y[popname])
#                        wspopsize.write(row, col, project.parsets[0].pars[0]['popsize'].p[popname][0])
                    maxcol = max(maxcol,col)
                col = 0
                
            wsprev.set_column(0, maxcol, colwidth) # Make wider
            wspopsize.set_column(0, maxcol, colwidth) # Make wider
                
            # Follow with program data.
            maxcol = 0
            row, col = 0, 0
            for row in xrange(copies+1):
                if row != 0:
                    wsalloc.write(row, col, '%s - District %i' % (project.name, row))
                for progkey in project.progsets[0].programs:
                    col += 1
                    if row == 0:
                        wsalloc.write(row, col, progkey)
                    else:
                        pass
#                        wsalloc.write(row, col, 0)
                    maxcol = max(maxcol,col)
                col = 0
                
            wsalloc.set_column(0, maxcol, colwidth) # Make wider
        
        # 4. Generate and save spreadsheet
        try:
            workbook.close()    
            warning('Multi-project template saved to "%s".' % spreadsheetpath)
        except:
            warning('Error: Template not saved due to a workbook error!')

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
        global guiportfolio, projectslistbox, guiobjectives, objectiveinputs
        projectpaths = []
        projectslist = []
        if guiportfolio is None: 
            guiportfolio = Portfolio()
        if not doadd:
            guiportfolio = Portfolio()
            projectslistbox.clear()
        filepaths = QtGui.QFileDialog.getOpenFileNames(caption='Choose project files', filter='*'+projext)
        if filepaths:
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
        global guiportfolio, guiobjectives
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
        global guiportfolio, guiobjectives, objectiveinputs
        starttime = time()
        for key in objectiveinputs.keys():
            guiobjectives[key] = eval(str(objectiveinputs[key].text())) # Get user-entered values
        guiobjectives['budget'] *= budgetfactor # Convert back to internal representation
        BOCobjectives = dcp(guiobjectives)
        guiportfolio.genBOCs(BOCobjectives, maxtime=3) # WARNING temp time
        guiportfolio.fullGA(guiobjectives, doplotBOCs=False, budgetratio = guiportfolio.getdefaultbudgets(), maxtime=3) # WARNING temp time
        warning('Geospatial analysis finished running; total time: %0.0f s' % (time() - starttime))
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
        if filepath:
            workbook = Workbook(filepath)
            worksheet = workbook.add_worksheet()
            
            # Define formatting
            originalblue = '#18C1FF' # analysis:ignore
            hotpink = '#FFC0CB' # analysis:ignore
            formats = dict()
            formats['plain'] = workbook.add_format({})
            formats['bold'] = workbook.add_format({'bold': True})
            formats['number'] = workbook.add_format({'bg_color': hotpink, 'num_format':0x04})
            colwidth = 30
            
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
                    thistxt = outlist[row][col]
                    thisformat = 'plain'
                    if col==0: thisformat = 'bold'
                    tmptxt = thistxt.lower()
                    for word in ['budget','outcome','allocation','initial','optimal','coverage']:
                        if tmptxt.find(word)>=0: thisformat = 'bold'
                    if col in [2,3] and thisformat=='plain': thisformat = 'number'
                    if thisformat=='number':thistxt = float(thistxt)
                    worksheet.write(row, col, thistxt, formats[thisformat])
            
            worksheet.set_column(0, 3, colwidth) # Make wider
            workbook.close()
            
            warning('Results saved to "%s".' % filepath)
        
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
        objectiveinputs[key].setText(str(guiobjectives[key]))
        objectiveinputs[key].move(left+120, 230+k*30)
    objectiveinputs['budget'].setText(str(guiobjectives['budget']/budgetfactor)) # So right units
    

    geoguiwindow.show()