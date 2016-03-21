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
    from optima import Project, Portfolio, loadobj, saveobj, odict, defaultobjectives, dcp, OptimaException, plotresults
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
        
        bestindex = 0        
        
        if len(project.parsets) > 0:
            try: project.parsets[-1].getresults()
            except: project.runsim(name=project.parsets[-1].name)
            
            copies, ok = QtGui.QInputDialog.getText(geoguiwindow, 'GA Spreadsheet Parameter', 'How many variants of the chosen project do you want?')
            try: copies = int(copies)
            except: raise OptimaException('Input cannot be converted into an integer.')
            
            refyear, ok = QtGui.QInputDialog.getText(geoguiwindow, 'GA Spreadsheet Parameter', 'Select a reference year for which you have district data.')
            refind = -1            
            try: refyear = int(refyear)
            except: raise OptimaException('Input cannot be converted into an integer.')
            if not refyear in [int(x) for x in project.parsets[-1].getresults().tvec]:
                raise OptimaException("Input not within range of years used by aggregate project's last stored calibration.")
            else:
                refind = [int(x) for x in project.parsets[-1].getresults().tvec].index(refyear)
            colwidth = 20
                
            ## 2. Get destination filename
            spreadsheetpath = QtGui.QFileDialog.getSaveFileName(caption='Save geospatial spreadsheet file', filter='*.xlsx')
            
            from xlsxwriter import Workbook
            from xlsxwriter.utility import xl_rowcol_to_cell as rc
            
            ## 3. Extract data needed from project (population names, program names...)
            if spreadsheetpath:
                workbook = Workbook(spreadsheetpath)
                wspopsize = workbook.add_worksheet('Population sizes')
                wsprev = workbook.add_worksheet('Population prevalence')
                
                nprogs = len(project.data['pops']['short'])
                
                # Start with pop and prev data.
                maxcol = 0
                row, col = 0, 0
                for row in xrange(copies+1):
                    if row != 0:
                        wspopsize.write(row, col, '%s - District %i' % (project.name, row))
                        wsprev.write(row, col, "='Population sizes'!%s" % rc(row,col))
                    for popname in project.data['pops']['short']:
                        col += 1
                        if row == 0:
                            wspopsize.write(row, col, popname)
                            wsprev.write(row, col, popname)
                        else:
                            wspopsize.write(row, col, "=%s*%s/%s" % (rc(copies+2,col),rc(row,nprogs+2),rc(copies+2,nprogs+2)))

                            # Prevalence scaling by function r/(r-1+1/x).
                            # If n is intended district prevalence and d is calibrated national prevalence, then...
                            # 'Unbound' (scaleup) ratio r is n(1-d)/(d(1-n)).
                            # Variable x is calibrated national prevalence specific to pop group.
                            natpopcell = rc(copies+2,col)
                            disttotcell = rc(row,nprogs+2)
                            nattotcell = rc(copies+2,nprogs+2)
                            wsprev.write(row, col, "=(%s*(1-%s)/(%s*(1-%s)))/(%s*(1-%s)/(%s*(1-%s))-1+1/%s)" % (disttotcell,nattotcell,nattotcell,disttotcell,disttotcell,nattotcell,nattotcell,disttotcell,natpopcell))

#                            # Prevalence scaling by function r/(r-1+1/x).
#                            # Variable r is ratio of intended district prevalence to calibrated national prevalence (scaleup factor).
#                            # Variable x is calibrated national prevalence specific to pop group.
#                            natpopcell = rc(copies+2,col)
#                            disttotcell = rc(row,nprogs+2)
#                            nattotcell = rc(copies+2,nprogs+2)
#                            wsprev.write(row, col, "=(%s/%s)/(%s/%s-1+1/%s)" % (disttotcell,nattotcell,disttotcell,nattotcell,natpopcell))
                            
#                            # Linear scaling.
#                            wsprev.write(row, col, "=%s*%s/%s" % (natpopcell,disttotcell,nattotcell))
                            
                        maxcol = max(maxcol,col)
                    col += 1
                    if row > 0:
                        wspopsize.write(row, col, "OR")
                        wsprev.write(row, col, "OR")
                    col += 1
                    if row == 0:
                        wspopsize.write(row, col, "Total (Intended)")
                        wsprev.write(row, col, "Total (Intended)")
                    col += 1
                    if row == 0:
                        wspopsize.write(row, col, "Total (Actual)")
                        wsprev.write(row, col, "Total (Actual)")
                    else:
                        wspopsize.write(row, col, "=SUM(%s:%s)" % (rc(row,1),rc(row,nprogs)))
                        wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(row,1),rc(row,nprogs),rc(row,1),rc(row,nprogs),rc(row,col)))
                    maxcol = max(maxcol,col)
                    col = 0
                
                # Just a check to make sure the sum and calibrated values match.
                # Using the last parset stored in project! Assuming it is the best calibration.
                row += 1              
                wspopsize.write(row, col, '---')
                wsprev.write(row, col, '---')
                row += 1
                wspopsize.write(row, col, 'Project Cal. %i' % refyear)
                wsprev.write(row, col, 'Project Cal. %i' % refyear)
                for popname in project.data['pops']['short']:
                    col += 1
                    wspopsize.write(row, col, project.parsets[-1].getresults().main['popsize'].pops[bestindex][col-1][refind])
                    wsprev.write(row, col, project.parsets[-1].getresults().main['prev'].pops[bestindex][col-1][refind])
                col += 2
                wspopsize.write(row, col, project.parsets[-1].getresults().main['popsize'].tot[bestindex][refind])
                wsprev.write(row, col, project.parsets[-1].getresults().main['prev'].tot[bestindex][refind])
                col += 1
                wspopsize.write(row, col, "=SUM(%s:%s)" % (rc(row,1),rc(row,nprogs)))
                wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(row,1),rc(row,nprogs),rc(row,1),rc(row,nprogs),rc(row,col)))  
                col = 0                
                
                row += 1
                wspopsize.write(row, col, 'District Aggregate')
                wsprev.write(row, col, 'District Aggregate')
                for popname in project.data['pops']['short']:
                    col += 1
                    wspopsize.write(row, col, '=SUM(%s:%s)' % (rc(1,col),rc(copies,col)))
                    wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(1,col),rc(copies,col),rc(1,col),rc(copies,col),rc(row,col)))
                col += 2
                wspopsize.write(row, col, '=SUM(%s:%s)' % (rc(1,col),rc(copies,col)))
                wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(1,col),rc(copies,col),rc(1,col),rc(copies,col),rc(row,col)))
                col += 1
                wspopsize.write(row, col, "=SUM(%s:%s)" % (rc(row,1),rc(row,nprogs)))
                wsprev.write(row, col, "=SUMPRODUCT('Population sizes'!%s:%s,%s:%s)/'Population sizes'!%s" % (rc(row,1),rc(row,nprogs),rc(row,1),rc(row,nprogs),rc(row,col)))  
                col = 0
                    
                wsprev.set_column(0, maxcol, colwidth) # Make wider
                wspopsize.set_column(0, maxcol, colwidth) # Make wider
                
                if len(project.progsets) > 0:
                    wsalloc = workbook.add_worksheet('Program allocations')
                    
                    # Follow with program data.
                    maxcol = 0
                    row, col = 0, 0
                    for row in xrange(copies+1):
                        if row != 0:
                            wsalloc.write(row, col, "='Population sizes'!%s" % rc(row,col))
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
                else:
                    warning('Warning: Loaded project is missing a program set.')
            
            # 4. Generate and save spreadsheet
            try:
                workbook.close()    
                warning('Multi-project template saved to "%s".' % spreadsheetpath)
            except:
                warning('Error: Template not saved due to a workbook error!')
        else:
            warning('Error: Loaded project is missing a parameter set!')

        return None
        
    # ONLY WORKS WITH VALUES IN THE TOTAL COLUMNS SO FAR!
    def makeproj():
        ''' Create a series of project files based on a seed file and a geospatial spreadsheet '''
        
        bestindex = 0   # This could be a problem down the road...
        
        checkplots = False       # To check if calibrations are rescaled nicely.
        
        ## 1. Load a project file -- WARNING, could be combined with the above!
        project = _loadproj()
        try: project.parsets[-1].getresults()
        except: project.runsim(name=project.parsets[-1].name)
        
        ## 2. Load a spreadsheet file
        spreadsheetpath = QtGui.QFileDialog.getOpenFileName(caption='Choose geospatial spreadsheet', filter='*.xlsx')
        print spreadsheetpath
        
        from xlrd import open_workbook  # For opening Excel workbooks.
        workbook = open_workbook(spreadsheetpath)
        wspopsize = workbook.sheet_by_name('Population sizes')
        wsprev = workbook.sheet_by_name('Population prevalence')
        
        ## 3. Get a destination folder
        destination = QtGui.QFileDialog.getExistingDirectory(caption='Choose output folder')
        
        ## 4. Read the spreadsheet
        poplist = []
        for colindex in xrange(wspopsize.ncols):
            if colindex > 0 and wspopsize.cell_value(0, colindex) not in ['','Total (Intended)','Total (Actual)']:
                poplist.append(wspopsize.cell_value(0, colindex))
        npops = len(poplist)
        
        districtlist = []
        popratio = odict()
        prevfactors = odict()
        plhivratio = odict()
        isdistricts = True
        for rowindex in xrange(wspopsize.nrows):
            if wspopsize.cell_value(rowindex, 0) == '---':
                isdistricts = False
            if isdistricts and rowindex > 0:
                districtlist.append(wspopsize.cell_value(rowindex, 0))
                
                # 'Actual' total ratios.
                if rowindex == 1:
                    popratio['tot'] = []
                    prevfactors['tot'] = []
                    plhivratio['tot'] = []
                popratio['tot'].append(wspopsize.cell_value(rowindex, npops+3))
                prevfactors['tot'].append(wsprev.cell_value(rowindex, npops+3))
                plhivratio['tot'].append(wspopsize.cell_value(rowindex, npops+3)*wsprev.cell_value(rowindex, npops+3))
                
                # Population group ratios.
                for popid in xrange(npops):
                    popname = poplist[popid]
                    colindex = popid + 1
                    if rowindex == 1:
                        popratio[popname] = []
                        prevfactors[popname] = []
                        plhivratio[popname] = []
                    popratio[popname].append(wspopsize.cell_value(rowindex, colindex))
                    prevfactors[popname].append(wsprev.cell_value(rowindex, colindex))
                    plhivratio[popname].append(wspopsize.cell_value(rowindex, colindex)*wsprev.cell_value(rowindex, colindex))
        print('Districts...')
        print districtlist
        ndistricts = len(districtlist)
        
        # Workout the reference year for the spreadsheet for later 'datapoint inclusion'.
        import re
        refind = -1
        try:
            refyear = int(re.sub("[^0-9]", "", wspopsize.cell_value(ndistricts+2, 0)))         
            if refyear in [int(x) for x in project.data['years']]:
                refind = [int(x) for x in project.data['years']].index(refyear)
                print('Reference year %i found in data year range with index %i.' % (refyear,refind))
            else:
                print('Reference year %i not found in data year range %i-%i.' % (refyear,int(project.data['years'][0]),int(project.data['years'][-1])))
        except:
            OptimaException('Warning: Cannot determine calibration reference year for this spreadsheet.')
        
        # Important note. Calibration value will be used as the denominator! So ratios can sum to be different from 1.
        # This allows for 'incomplete' subdivisions, e.g. a country into 2 of 3 states.
        popdenom = wspopsize.cell_value(ndistricts+2, npops+3)
        popratio['tot'] = [x/popdenom for x in popratio['tot']]
        prevdenom = wsprev.cell_value(ndistricts+2, npops+3)
        prevfactors['tot'] = [x/prevdenom for x in prevfactors['tot']]
        plhivdenom = wspopsize.cell_value(ndistricts+2, npops+3)*wsprev.cell_value(ndistricts+2, npops+3)
        plhivratio['tot'] = [x/plhivdenom for x in plhivratio['tot']]        
        for popid in xrange(npops):
            colindex = popid + 1
            popname = poplist[popid]
            popdenom = wspopsize.cell_value(ndistricts+2, colindex)
            popratio[popname] = [x/popdenom for x in popratio[popname]]
            prevdenom = wsprev.cell_value(ndistricts+2, colindex)
            prevfactors[popname] = [x/prevdenom for x in prevfactors[popname]]
            plhivdenom = wspopsize.cell_value(ndistricts+2, colindex)*wsprev.cell_value(ndistricts+2, colindex)
            plhivratio[popname] = [x/plhivdenom for x in plhivratio[popname]]

        print('Population ratio...')
        print popratio                     # Proportions of national population split between districts.
        print('Prevalence multiples...')
        print prevfactors                   # Factors by which to multiply prevalence in a district.        
        print('PLHIV ratio...')
        print plhivratio                    # Proportions of PLHIV split between districts.
        
        ## 5. Calibrate each project file according to the data entered for it in the spreadsheet
        projlist = []
        c = 0
        for districtname in districtlist:
            newproject = dcp(project)
            newproject.name = districtname
            
            ### ------------------------- WHERE DATA AND PARSET MUST BE RESCALED (AND PROGSET EVENTUALLY)
            # NOTE: Scaling assumptions for popsize & prev are POPGROUP-dependent, while everything else is TOT-dependent!                
            
            # Scale data.            
            for popid in xrange(npops):
                popname = poplist[popid]
                for x in newproject.data['popsize']:
                    x[popid] = [z*popratio[popname][c] for z in x[popid]]
                for x in newproject.data['hivprev']:
                    x[popid] = [z*prevfactors[popname][c] for z in x[popid]]
            newproject.data['numcirc'] = [[y*plhivratio['tot'][c] for y in x] for x in newproject.data['numcirc']]
            newproject.data['numtx'] = [[y*plhivratio['tot'][c] for y in x] for x in newproject.data['numtx']]
            newproject.data['numpmtct'] = [[y*plhivratio['tot'][c] for y in x] for x in newproject.data['numpmtct']]
            newproject.data['numost'] = [[y*plhivratio['tot'][c] for y in x] for x in newproject.data['numost']]
            
            # Scale calibration.
            for popid in xrange(npops):
                popname = poplist[popid]
                newproject.parsets[-1].pars[bestindex]['popsize'].p[popname][0] *= popratio[popname][c]
                newproject.parsets[-1].pars[bestindex]['initprev'].y[popname] *= prevfactors[popname][c]
                newproject.parsets[-1].pars[bestindex]['numcirc'].y[popname] *= plhivratio['tot'][c]
            newproject.parsets[-1].pars[bestindex]['numtx'].y['tot'] *= plhivratio['tot'][c]
            newproject.parsets[-1].pars[bestindex]['numpmtct'].y['tot'] *= plhivratio['tot'][c]
            newproject.parsets[-1].pars[bestindex]['numost'].y['tot'] *= plhivratio['tot'][c]
            
            # Scale programs.
            if len(project.progsets) > 0:
                for progid in newproject.progsets[-1].programs:
                    program = newproject.progsets[-1].programs[progid]
                    program.costcovdata['cost'] = [x*plhivratio['tot'][c] for x in program.costcovdata['cost']]
                    if not program.costcovdata['coverage'] == [None]:
                        program.costcovdata['coverage'] = [x*plhivratio['tot'][c] for x in program.costcovdata['coverage']]
                
            ### -----------------------------------------------------------------------------------------

#            # Don't forget to place a data point corresponding to pop/prev from spreadsheets!
#            # NOTE: Currently doesn't work because some parts of the the data structure may have 1 element for assumptions only!           
#            if not refind == -1:
#                for popid in xrange(npops):
#                    newproject.data['popsize'][bestindex][popid][refind] = wspopsize.cell_value(c+1, popid+1)
#                    newproject.data['hivprev'][bestindex][popid][refind] = wsprev.cell_value(c+1, popid+1)
#            else:
#                print('Absolute values in spreadsheet were for non-data-period reference year %i. Thus not used for autofit.' % refyear)
            
#            # Autocalibrate FOI of district calibration to match linearly-rescaled national calibration curves.
#            tempprev = dcp(newproject.data['hivprev'])
            datayears = len(newproject.data['years'])
#            psetname = newproject.parsets[-1].name
            # WARNING: Converting results to data assumes that results is already in yearly-dt form.
            newproject.data['hivprev'] = [[[z*prevfactors[poplist[yind]][c] for z in y[0:datayears]] for yind, y in enumerate(x)] for x in project.parsets[-1].getresults().main['prev'].pops]
#            newproject.autofit(name=psetname, orig=psetname, fitwhat=['force'], maxtime=None, maxiters=10, inds=None) # Run automatic fitting and update calibration
#            
#            newproject.data['hivprev'] = tempprev    
#            
            newproject.runsim(newproject.parsets[-1].name) # Re-simulate autofit curves, but for old data.
            projlist.append(newproject)
            c += 1
        project.runsim(project.parsets[-1].name)
        
        ## 6. Save each project file into the directory
#        if checkplots: plotresults(project.parsets[-1].getresults(), toplot=['popsize-tot', 'popsize-pops']) 
        if checkplots: 
            plotresults(project.parsets[-1].getresults(), toplot=['popsize-tot', 'popsize-pops'])
            plotresults(project.parsets[-1].getresults(), toplot=['prev-tot', 'prev-pops'])
        for subproject in projlist:
#            if checkplots: plotresults(subproject.parsets[-1].getresults(), toplot=['popsize-tot', 'popsize-pops'])
            if checkplots:
                plotresults(subproject.parsets[-1].getresults(), toplot=['popsize-tot', 'popsize-pops'])
                plotresults(subproject.parsets[-1].getresults(), toplot=['prev-tot', 'prev-pops'])
            saveobj(subproject.name+'.prj', subproject)
            
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
            except Exception as E: 
                warning('Could not load file "%s" because "%s"' % (filepath, E.message))
                import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
                return None
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
        guiportfolio.genBOCs(BOCobjectives, maxtime=2) # WARNING temp time
        guiportfolio.fullGA(guiobjectives, doplotBOCs=False, budgetratio = guiportfolio.getdefaultbudgets(), maxtime=3) # WARNING temp time
        warning('Geospatial analysis finished running; total time: %0.0f s' % (time() - starttime))
        return None
        
        
    def plotgeo():
        ''' Actually plot geospatial analysis!!! '''
        global guiportfolio
        if guiportfolio is None: 
            warning('Please load a portfolio first')
            return None
        gaoptim = guiportfolio.gaoptims[-1]
        guiportfolio.plotBOCs(objectives=gaoptim.objectives, initbudgets=gaoptim.getinitbudgets(), optbudgets=gaoptim.getoptbudgets(), deriv=False)
                
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
    buttons['plotgeo']   = QtGui.QPushButton('Plot geospatial results', parent=geoguiwindow)
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
    actions['plotgeo']   = plotgeo
    actions['export']    = export
    actions['saveport']  = saveport
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