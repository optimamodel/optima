"""
GEOSPATIAL

This file defines everything needed for the Python GUI for geospatial analysis.

Version: 2016nov03
"""

from optima import Project, Portfolio, loadproj, loadobj, saveobj, odict, defaultobjectives, dcp, OptimaException, plotresults, printv
from PyQt4 import QtGui
from pylab import figure, close, array
from time import time
import os


global geoguiwindow, globalportfolio
if 1:  geoguiwindow, globalportfolio = [None]*2

globalobjectives = defaultobjectives(verbose=0)
globalobjectives['budget'] = 0.0 # Reset

    
    
## Global options
budgetfactor = 1e6 # Conversion between screen and internal
projext = '.prj'
portext = '.prt'



##############################################################################################################################
## Define functions
##############################################################################################################################





def _loadproj(filepath=None, usegui=True):
    ''' Helper function to load a project, since used more than once '''
    if filepath == None and usegui:
        filepath = QtGui.QFileDialog.getOpenFileName(caption='Choose project file', filter='*'+projext)
    project = None
    if filepath:
        try: project = loadproj(filepath, verbose=0)
        except Exception as E: print('Could not load file "%s": "%s"' % (filepath, E.message))
        if type(project)==Project: return project
        else: print('File "%s" is not an Optima project file' % filepath)
    else:
        print('No filepath provided')
    return None


def resetbudget():
    ''' Replace current displayed budget with default from portfolio '''
    global globalportfolio, objectiveinputs
    totalbudget = 0
    for project in globalportfolio.projects.values():
        totalbudget += sum(project.progsets[0].getdefaultbudget().values())
    objectiveinputs['budget'].setText(str(totalbudget/budgetfactor))
    return None

def warning(message, usegui=True):
    global geoguiwindow
    if usegui:
        QtGui.QMessageBox.warning(geoguiwindow, 'Message', message)
    else:
        print(message)
    
    
# WARNING: HARDCODING -1TH PROGSET AND PARSET THROUGHOUT. CHECK WITH CLIFF.
def gui_makesheet():
    ''' GUI wrapper to create a geospatial spreadsheet template based on a project file '''
    makesheet(usegui=True)
    
def makesheet(projectpath=None, spreadsheetpath=None, copies=None, refyear=None, usegui=False):
    ''' Create a geospatial spreadsheet template based on a project file '''
    ''' copies - Number of low-level projects to subdivide a high-level project into (e.g. districts in nation) '''      
    ''' refyear - Any year that exists in the high-level project calibration for which low-level project data exists '''    
    
    ## 1. Load a project file
    project = _loadproj(projectpath, usegui)
    if project == None:
        raise OptimaException('No project loaded.')
    
    bestindex = 0 # Index of the best result -- usually 0 since [best, low, high]  
    
    if len(project.parsets) > 0:
        try: project.parsets[-1].getresults()
        except: project.runsim(name=project.parsets[-1].name)
        
        if usegui:
            copies, ok = QtGui.QInputDialog.getText(geoguiwindow, 'GA Spreadsheet Parameter', 'How many variants of the chosen project do you want?')
        try: copies = int(copies)
        except: raise OptimaException('Input (number of project copies) cannot be converted into an integer.')
        
        if usegui:
            refyear, ok = QtGui.QInputDialog.getText(geoguiwindow, 'GA Spreadsheet Parameter', 'Select a reference year for which you have district data.')
        refind = -1            
        try: refyear = int(refyear)
        except: raise OptimaException('Input (reference year) cannot be converted into an integer.')
        if not refyear in [int(x) for x in project.parsets[-1].getresults().tvec]:
            raise OptimaException("Input not within range of years used by aggregate project's last stored calibration.")
        else:
            refind = [int(x) for x in project.parsets[-1].getresults().tvec].index(refyear)
        colwidth = 20
            
        ## 2. Get destination filename
        if usegui:
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
                warning('Warning: Loaded project is missing a program set.', usegui)
        
        # 4. Generate and save spreadsheet
        try:
            workbook.close()    
            warning('Multi-project template saved to "%s".' % spreadsheetpath, usegui)
        except:
            warning('Error: Template not saved due to a workbook error!', usegui)
    else:
        warning('Error: Loaded project is missing a parameter set!', usegui)

    return None
    
def gui_makeproj():
    ''' Wrapper to create a series of project files based on a seed file and a geospatial spreadsheet '''
    makeproj(usegui=True)
    
    
# ONLY WORKS WITH VALUES IN THE TOTAL COLUMNS SO FAR!
def makeproj(projectpath=None, spreadsheetpath=None, destination=None, checkplots=False, usegui=False, verbose=2):
    ''' Create a series of project files based on a seed file and a geospatial spreadsheet '''
    ''' checkplots - To check if calibrations are rescaled nicely. '''
    
    bestindex = 0   # This could be a problem down the road...
    
    ## 1. Load a project file -- WARNING, could be combined with the above!
    project = _loadproj(projectpath, usegui)
    if project == None:
        raise OptimaException('No project loaded.')
    try: project.parsets[-1].getresults()
    except: project.runsim(name=project.parsets[-1].name)
    
    ## 2. Load a spreadsheet file
    if usegui:
        spreadsheetpath = QtGui.QFileDialog.getOpenFileName(caption='Choose geospatial spreadsheet', filter='*.xlsx')
    print('Spreadsheet path: %s' % spreadsheetpath)
    
    from xlrd import open_workbook  # For opening Excel workbooks.
    workbook = open_workbook(spreadsheetpath)
    wspopsize = workbook.sheet_by_name('Population sizes')
    wsprev = workbook.sheet_by_name('Population prevalence')
    
    ## 3. Get a destination folder
    if usegui:
        destination = QtGui.QFileDialog.getExistingDirectory(caption='Choose output folder')
    print destination
    
    # Create it if it doesn't exist
    try:
        if not os.path.exists(destination):
            os.makedirs(destination)
    except: print('Was unable to make target directory "%s"' % destination)
    
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

    printv('Population ratio...', 4, verbose)
    printv(popratio, 4, verbose)                     # Proportions of national population split between districts.
    printv('Prevalence multiples...', 4, verbose)
    printv(prevfactors, 4, verbose)                   # Factors by which to multiply prevalence in a district.        
    printv('PLHIV ratio...', 4, verbose)
    printv(plhivratio, 4, verbose)                    # Proportions of PLHIV split between districts.
    
    ## 5. Calibrate each project file according to the data entered for it in the spreadsheet
    projlist = []
    for c,districtname in enumerate(districtlist):
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
            newproject.parsets[-1].pars[bestindex]['popsize'].i[popname] *= popratio[popname][c]
            newproject.parsets[-1].pars[bestindex]['initprev'].y[popname] *= prevfactors[popname][c]
            newproject.parsets[-1].pars[bestindex]['numcirc'].y[popname] *= plhivratio['tot'][c]
        newproject.parsets[-1].pars[bestindex]['numtx'].y['tot'] *= plhivratio['tot'][c]
        newproject.parsets[-1].pars[bestindex]['numpmtct'].y['tot'] *= plhivratio['tot'][c]
        newproject.parsets[-1].pars[bestindex]['numost'].y['tot'] *= plhivratio['tot'][c]
        
        # Scale programs.
        if len(project.progsets) > 0:
            for progid in newproject.progsets[-1].programs:
                program = newproject.progsets[-1].programs[progid]
                program.costcovdata['cost'] = popratio['tot'][c]*array(program.costcovdata['cost'],dtype=float)
                if not program.costcovdata['coverage'] == [None]:
                    program.costcovdata['coverage'] = popratio['tot'][c]*array(program.costcovdata['coverage'],dtype=float)
            
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
        saveobj(destination+os.sep+subproject.name+'.prj', subproject)
        
    return None

def gui_create():
    ''' Wrapper to create a portfolio by selecting a list of projects; silently skip files that fail '''
    create(usegui=True)

def create(filepaths=None, portfolio=None, doadd=False, usegui=False):
    ''' Create a portfolio by selecting a list of projects; silently skip files that fail '''
    if usegui: global globalportfolio, projectslistbox, globalobjectives, objectiveinputs
    
    projectpaths = []
    projectslist = []
    if globalportfolio is None: 
        globalportfolio = Portfolio()
    if not doadd:
        globalportfolio = Portfolio()
        if usegui:
            projectslistbox.clear()
    if doadd and portfolio != None:
        globalportfolio = portfolio
    if usegui:
        filepaths = QtGui.QFileDialog.getOpenFileNames(caption='Choose project files', filter='*'+projext)
    if filepaths:
        if type(filepaths)==str: filepaths = [filepaths] # Convert to list
        for filepath in filepaths:
            tmpproj = None
            try: tmpproj = loadproj(filepath, verbose=0)
            except: print('Could not load file "%s"; moving on...' % filepath)
            if tmpproj is not None: 
                try: 
                    assert type(tmpproj)==Project
                    projectslist.append(tmpproj)
                    projectpaths.append(filepath)
                    print('Project file "%s" loaded' % filepath)
                except: print('File "%s" is not an Optima project file; moving on...' % filepath)
        if usegui:
            projectslistbox.addItems(projectpaths)
        globalportfolio.addprojects(projectslist)
        if usegui:
            resetbudget() # And reset the budget
    if usegui:
        return None
    else:
        return dcp(globalportfolio)


def gui_addproj():
    ''' Wrappeer to add a project -- same as creating a portfolio except don't overwrite '''
    addproj(usegui=True)

def addproj(portfolio=None, filepaths=None, usegui=False):
    ''' Add a project -- same as creating a portfolio except don't overwrite '''
    p = create(filepaths=filepaths, doadd=True, portfolio=portfolio, usegui=usegui)
    if usegui:
        resetbudget() # And reset the budget
    return p


def gui_loadport():
    ''' GUI wrapper to load an existing portfolio '''
    loadport(usegui=True)
    
def loadport(filepath=None, usegui=False):
    ''' Load an existing portfolio '''
    if usegui: global globalportfolio, projectslistbox
    if usegui:
        filepath = QtGui.QFileDialog.getOpenFileName(caption='Choose portfolio file', filter='*'+portext)
    tmpport = None
    if filepath:
        try: tmpport = loadobj(filepath, verbose=0)
        except Exception as E: 
            warning('Could not load file "%s" because "%s"' % (filepath, E.message), usegui)
            import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
            return None
        if tmpport is not None: 
            if type(tmpport)==Portfolio:
                globalportfolio = tmpport
                if usegui:
                    projectslistbox.clear()
                    projectslistbox.addItems([proj.name for proj in globalportfolio.projects.values()])
                print('Portfolio file "%s" loaded' % filepath)
            else: print('File "%s" is not an Optima portfolio file' % filepath)
    else:
        warning('File path not provided. Portfolio not loaded.', usegui)
    if usegui:
        resetbudget() # And reset the budget
        return None
    else:
        return dcp(globalportfolio)


def gui_rungeo():
    ''' Wrapper to actually run geospatial analysis!!! '''
    rungeo(usegui=True)

def rungeo(portfolio=None, objectives=None, BOCtime=300, maxtime=120, usegui=False):
    ''' Actually run geospatial analysis!!! '''
    if usegui: global globalportfolio, globalobjectives, objectiveinputs
    starttime = time()
    if portfolio != None:
        globalportfolio = portfolio
    if objectives != None:
        globalobjectives = objectives
    if usegui:
        for key in objectiveinputs.keys():
            globalobjectives[key] = eval(str(objectiveinputs[key].text())) # Get user-entered values
        globalobjectives['budget'] *= budgetfactor # Convert back to internal representation
    BOCobjectives = dcp(globalobjectives)
    globalportfolio.genBOCs(BOCobjectives, maxtime=BOCtime)
    globalportfolio.fullGA(globalobjectives, doplotBOCs=False, budgetratio = globalportfolio.getdefaultbudgets(), maxtime=maxtime) # WARNING temp time
    warning('Geospatial analysis finished running; total time: %0.0f s' % (time() - starttime), usegui)
    if usegui: 
        return None
    else:
        return dcp(globalportfolio)
    
def gui_plotgeo():
    ''' Wrapper to actually plot geospatial analysis!!! '''
    plotgeo(usegui=True)

def plotgeo(usegui=False):
    ''' Actually plot geospatial analysis!!! '''
    global globalportfolio
    if globalportfolio is None: 
        warning('Please load a portfolio first', usegui)
        return None
    gaoptim = globalportfolio.gaoptims[-1]

    # Handles multithreading-based resorting. WARNING: Is based on simple sorting UIDs. Expect problems if there are mismatched UIDs...
    projlist = [x.uid for x in globalportfolio.projects.values()]
    pairlist = [x[0].project.uid for x in gaoptim.resultpairs.values()]
    projids = [x[0] for x in sorted(enumerate(projlist), key=lambda pair: pair[1])]
    pairids = [x[0] for x in sorted(enumerate(pairlist), key=lambda pair: pair[1])]
    truecid = [x[1] for x in sorted(zip(pairids,projids))]      # Transforms from pair to project ordering.
    
    
    extrax = [None]*len(gaoptim.resultpairs); 
    extray = [None]*len(gaoptim.resultpairs);
    for cid in xrange(len(gaoptim.resultpairs)):
#        extrax.append([]); extray.append([]);
        rp = gaoptim.resultpairs[cid]
        extrax[truecid[cid]] = []
        extray[truecid[cid]] = []
        extrax[truecid[cid]].append(rp['init'].budget['Current allocation'][:].sum())
        extrax[truecid[cid]].append(rp['opt'].budget['Optimal allocation'][:].sum())
        extray[truecid[cid]].append(rp['init'].improvement[-1][0])
        extray[truecid[cid]].append(rp['opt'].improvement[-1][-1])
    
    globalportfolio.plotBOCs(objectives=gaoptim.objectives, 
                          initbudgets=[x[1] for x in sorted(zip(truecid,gaoptim.getinitbudgets()))], 
                          optbudgets=[x[1] for x in sorted(zip(truecid,gaoptim.getoptbudgets()))], 
                          deriv=False, extrax=extrax, extray=extray)
            
    return None

def gui_export():
    ''' Wrapper to save the current results to Excel file '''
    export(usegui=True)

def export(portfolio=None, filepath=None, usegui=False):
    ''' Save the current results to Excel file '''
    if usegui: global globalportfolio
    
    if portfolio is not None:
        globalportfolio = portfolio
        if filepath is None:
            filepath = portfolio.name+'.prt'
    if type(globalportfolio)!=Portfolio and usegui: warning('Warning, must load portfolio first!')
    
    from xlsxwriter import Workbook
    if not usegui: print('Saving portfolio...')
    
    # 1. Extract data needed from portfolio
    try:
        outstr = globalportfolio.gaoptims[-1].printresults() # Stored, but regenerate
    except:
        errormsg = 'Warning, it does not seem that geospatial analysis has been run for this portfolio!'
        warning(errormsg, usegui)
        if not usegui: raise Exception(errormsg)
        return None
    
    # 2. Create a new file dialog to save this spreadsheet
    if usegui:
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
        
        warning('Results saved to "%s".' % filepath, usegui)
    else:
        warning('Filepath not supplied: %s' % filepath, usegui)
    
    return None
    

def gui_saveport():
    ''' Wrapper to save the current portfolio '''
    saveport(usegui=True)

def saveport(portfolio = None, filepath = None, usegui=False):
    ''' Save the current portfolio '''
    if usegui: global globalportfolio
    if portfolio != None:
        globalportfolio = portfolio
    if usegui:
        filepath = QtGui.QFileDialog.getSaveFileName(caption='Save portfolio file', filter='*'+portext)
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
#    globalobjectives = defaultobjectives()
#    globalobjectives['budget'] = 0.0 # Reset
    
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