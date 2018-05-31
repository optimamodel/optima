###########################################################################
## Preliminaries
###########################################################################

from optima import OptimaException, loaddatapars, odict, printv, today, isnumber, makefilepath, version, compareversions
from numpy import nan, isnan, array, shape # For reading in empty values
from xlrd import open_workbook, colname # For opening Excel workbooks
versioncheck = '\n(spreadsheet version not available)' # To be filled once the version is checked below


def forcebool(entry, location=''):
    ''' Convert an entry to be Boolean '''
    if   entry in [1, 'TRUE',  'true',  'True',  't', 'T']: return 1
    elif entry in [0, 'FALSE', 'false', 'False', 'f', 'F']: return 0
    else:
        errormsg = 'Boolean data "%s" not understood in spreadsheet location "%s"' % (entry, location)
        raise OptimaException(errormsg)
    
    
def validatedata(thesedata, sheetname, thispar, row, checkupper=False, checklower=True, checkblank=True, startcol=0):
    ''' Do basic validation on the data: at least one point entered, between 0 and 1 or just above 0 if checkupper=False '''
    
    # Check that only numeric data have been entered
    for column,datum in enumerate(thesedata):
        if not isnumber(datum):
            errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
            errormsg += 'row=%i, column=%s, value="%s"\n' % (row+1, colname(column+startcol), datum)
            errormsg += 'Be sure all entries are numeric'
            errormsg += versioncheck
            if ' ' or '\t' in datum: errormsg +=' (there seems to be a space or tab)'
            raise OptimaException(errormsg)
    
    # Now check integrity of data itself
    validdata = array(thesedata)[~isnan(thesedata)]
    if len(validdata):
        valid = array([True]*len(validdata)) # By default, set everything to valid
        if checklower: valid *= array(validdata)>=0
        if checkupper: valid *= array(validdata)<=1
        if not valid.all():
            invalid = validdata[valid==False]
            errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
            errormsg += 'row=%i, invalid="%s", values="%s"\n' % (row+1, invalid, validdata)
            errormsg += 'Be sure that all values are >=0 (and <=1 if a probability)'
            errormsg += versioncheck
            raise OptimaException(errormsg)
    elif checkblank: # No data entered
        errormsg = 'No data or assumption entered for sheet "%s", parameter "%s", row=%i' % (sheetname, thispar, row) 
        errormsg += versioncheck
        raise OptimaException(errormsg)
    else:
        return None


def blank2nan(thesedata):
    ''' Convert a blank entry to a nan '''
    return list(map(lambda val: nan if val=='' else val, thesedata))
    

def getyears(sheetdata):
    ''' Get years from a worksheet'''
    years = [] # Initialize epidemiology data years
    for col in range(sheetdata.ncols):
        thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
        if thiscell=='' and len(years)>0: #  We've gotten to the end
            lastdatacol = col # Store this column number
            break # Quit
        elif thiscell != '': # Nope, more years, keep going
            years.append(float(thiscell)) # Add this year
    
    return lastdatacol, years
    

###########################################################################################################
## Define the workbook and parameter names -- should match makespreadsheet.py and partable in parameters.py
###########################################################################################################
        
def loadspreadsheet(filename=None, folder=None, verbose=2):
    '''
    Loads the spreadsheet (i.e. reads its contents into the data).
    This data sheet is used in the next step to update the corresponding model.
    
    Version: 1.5 (2017feb09)
    '''
    
    fullpath = makefilepath(filename=filename, folder=folder, ext='xlsx', default='simple.xlsx')
    
    printv('Loading data from %s...' % fullpath, 1, verbose)
    
    # Create dictionary of parameters to load
    pardefinitions = loaddatapars(verbose=verbose)
    sheets     = pardefinitions['sheets']
    sheettypes = pardefinitions['sheettypes']
    checkupper = pardefinitions['checkupper']
    
    ## Initialize dictionaries
    data = odict() # Create sheetsure for holding data
    data['meta'] = odict()
    data['meta']['datacomments'] = [] # Store the data comments entered on the instructions sheet
    data['meta']['date'] = today()
    data['meta']['sheets'] = sheets # Store parameter names
    
    ## Initialize populations
    data['pops'] = odict() # Initialize to empty list
    data['pops']['short'] = [] # Store short population/program names, e.g. "FSW"
    data['pops']['long'] = [] # Store long population/program names, e.g. "Female sex workers"
    data['pops']['male'] = [] # Store whether or not population is male
    data['pops']['female'] = [] # Store whether or not population is female
    data['pops']['age'] = [] # Store the age range for this population
    
    ## Initialize partnerships
    data['pships'] = odict() # Initialize to empty list
    data['pships']['reg'] = [] # Store regular partnerships
    data['pships']['cas'] = [] # Store casual partnerships
    data['pships']['com'] = [] # Store commercial partnerships
    data['pships']['inj'] = [] # Store injecting partnerships
    
    ## Initialize other quantities
    blhindices = {'best':0, 'low':1, 'high':2} # Define best-low-high indices
    skipblanksheets = ['Optional indicators', 'Cascade'] # Don't check optional indicators, check everything else
    skipblankpars = ['numcirc']
    
    ## Actually open workbook
    try:  workbook = open_workbook(fullpath) # Open workbook
    except Exception as E: 
        errormsg = 'Failed to load spreadsheet "%s": %s' % (fullpath, repr(E))
        raise OptimaException(errormsg)
    
    
    ## Open workbook and calculate columns for which data are entered, and store the year ranges
    sheetdata = workbook.sheet_by_name('Population size') # Load this workbook
    lastdatacol, data['years'] = getyears(sheetdata)
    assumptioncol = lastdatacol + 1 # Figure out which column the assumptions are in; the "OR" space is in between
    
    ##################################################################
    ## Now, actually load the data
    ##################################################################    
    
    ## Load comment and version from front sheet
    printv('Loading comment and version...', 3, verbose)
    instructionssheet = workbook.sheet_by_name('Instructions')
    versionrow = 8
    commentrow = 16 # First row for comments
    if instructionssheet.nrows >= commentrow:
        for row in range(commentrow-1, instructionssheet.nrows):
            comment = instructionssheet.cell_value(row, 0) # Hardcoded comment cell in A14
            data['meta']['datacomments'].append(comment) # Store the data comment entered on the instructions sheet
    versioncell = instructionssheet.cell_value(versionrow, 0)
    versionstr = versioncell.split()[-1] # Last bit should be the version
    if compareversions(versionstr, version) != 0:
        versioncheck = '\nNote: spreadsheet version does not match Optima version: %s vs. %s' % (versionstr, version)
        printv(versioncheck, 1, verbose)
    else:
        versioncheck = '\nHowever, spreadsheet and Optima versions match (%s = %s)' % (versionstr, version)
    
    ## Load population data
    printv('Loading populations...', 3, verbose)
    popssheet = workbook.sheet_by_name('Populations')
    for row in range(popssheet.nrows):
        thesedata = popssheet.row_values(row, start_colx=2, end_colx=11) # Data starts in 3rd column, finishes in 11th column
        subparam  = popssheet.cell_value(row, 1) # Figure out which population it is
        if subparam != '': # Warning -- ugly to duplicate this, but doesn't follow the format of data sheets, either
            printv('Loading population "%s"...' % subparam, 4, verbose)
            data['pops']['short'].append(str(thesedata[0]))
            data['pops']['long'].append(str(thesedata[1]))
            data['pops']['male'].append(forcebool(thesedata[2], 'male, row %i'% row))
            data['pops']['female'].append(forcebool(thesedata[3], 'female, row %i'% row))
            data['pops']['age'].append([int(thesedata[4]), int(thesedata[5])])
    
    ## Loop over each group of data sheets
    for sheetname in sheets.keys(): # Loop over each type of data, but treat constants differently
        subparlist = sheets[sheetname] # List of subparameters
        sheetdata = workbook.sheet_by_name(sheetname) # Load this workbook
        sheettype = sheettypes[sheetname] # Get the type of this sheet -- e.g., is it a time parameter or a matrix?
        printv('Loading sheet "%s"...' % sheetname, 3, verbose)
        
        # Loop over each row in the workbook, starting from the top
        for row in range(sheetdata.nrows): 
            paramcategory = sheetdata.cell_value(row,0) # See what's in the first column for this row
            subparam = sheetdata.cell_value(row, 1) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
            
            if paramcategory != '': # It's not blank: e.g. "HIV prevalence"
                printv('Loading parameter "%s"...' % paramcategory, 3, verbose)
                
                # It's anything other than the constants sheet: create an empty list
                if sheettype != 'constant': 
                    try:
                        thispar = subparlist.pop(0) # Get the name of this parameter, e.g. 'popsize'
                    except:
                        errormsg = 'Incorrect number of headings found for sheet "%s"\n' % sheetname
                        errormsg += 'Check that there is no extra text in the first two columns'
                        errormsg += versioncheck
                        raise OptimaException(errormsg)
                    data[thispar] = [] # Initialize to empty list
            
            elif subparam != '': # The second column isn't blank: it's time for the data
                printv('Parameter: %s' % subparam, 4, verbose)
                
                # It's key data, save both the values and uncertainties
                if sheettype=='key':
                    startcol = 3 # Extra column for high/best/low
                    if len(data[thispar])==0: 
                        data[thispar] = [[] for z in range(3)] # Create new variable for best, low, high
                    thesedata = blank2nan(sheetdata.row_values(row, start_colx=startcol, end_colx=lastdatacol)) # Data starts in 4th column -- need room for high/best/low
                    assumptiondata = sheetdata.cell_value(row, assumptioncol)
                    if assumptiondata != '': thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                    blh = sheetdata.cell_value(row, 2) # Read in whether indicator is best, low, or high
                    data[thispar][blhindices[blh]].append(thesedata) # Actually append the data
                    validatedata(thesedata, sheetname, thispar, row, checkblank=(blh=='best'), checkupper=checkupper[thispar], startcol=startcol)  # Make sure at least the best estimate isn't blank
                    
                # It's basic data, append the data and check for programs
                elif sheettype=='time': 
                    startcol = 2
                    thesedata = blank2nan(sheetdata.row_values(row, start_colx=startcol, end_colx=lastdatacol-1)) # Data starts in 3rd column, and ends lastdatacol-1
                    assumptiondata = sheetdata.cell_value(row, assumptioncol-1)
                    if assumptiondata != '': # There's an assumption entered
                        thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                    data[thispar].append(thesedata) # Store data
                    checkblank = False if sheetname in skipblanksheets or thispar in skipblankpars else True # Don't check optional indicators, check everything else
                    validatedata(thesedata, sheetname, thispar, row, checkblank=checkblank, checkupper=checkupper[thispar], startcol=startcol)

                # It's a matrix, append the data                                     
                elif sheettype=='matrix':
                    startcol = 2
                    thesedata = sheetdata.row_values(row, start_colx=startcol, end_colx=sheetdata.ncols) # Data starts in 3rd column
                    thesedata = list(map(lambda val: 0 if val=='' else val, thesedata)) # Replace blanks with 0
                    data[thispar].append(thesedata) # Store data
                    validatedata(thesedata, sheetname, thispar, row, startcol=startcol)
                
                # It's a constant, create a new dictionary entry
                elif sheettype=='constant':
                    startcol = 2
                    endcol = 5
                    try:
                        thispar = subparlist.pop(0) # Get the first item in this list
                    except Exception as E:
                        errormsg = 'Error reading constants sheet: perhaps too many rows?\n'
                        errormsg += '%s' % repr(E)
                        errormsg += versioncheck
                        raise OptimaException(errormsg)
                    thesedata = blank2nan(sheetdata.row_values(row, start_colx=startcol, end_colx=endcol)) # Data starts in 3rd column, finishes in 5th column
                    validatedata(thesedata, sheetname, thispar, row)
                    data[thispar] = thesedata # Store data
                
                # It's not recognized: throw an error
                else: 
                    errormsg = 'Sheet type "%s" not recognized: please do not change the names of the sheets!' % sheettype
                    raise OptimaException(errormsg)
    
    # Check that matrices have correct shape
    data['npops'] = len(data['pops']['short'])
    for key in sheets['Partnerships & transitions']:
        thesedata = data[key]
        matrixshape = shape(array(thesedata))
        correctfirstdim = data['npops'] if key!='birthtransit' else sum(data['pops']['female'])
        correctseconddim = data['npops']
        if matrixshape[0] != correctfirstdim or matrixshape[1] != correctseconddim:
            errormsg = 'Matrix "%s" in partnerships & transitions sheet is not the correct shape' % key
            errormsg += '(rows = %i, columns = %i, should be %i and %i)\n' % (matrixshape[0], matrixshape[1], correctfirstdim, correctseconddim)
            errormsg += 'Check for missing rows or added text'
            errormsg += versioncheck
            raise OptimaException(errormsg)
    
    # Store tuples of partnerships
    popkeys = data['pops']['short']
    for row in range(data['npops']):
        for col in range(data['npops']):
            for key in ['reg', 'cas', 'com', 'inj']:
                if data['part'+key][row][col]: data['pships'][key].append((popkeys[row],popkeys[col]))
    
    # Do a final check
    failedtopopulate = odict()
    for sheetname,sheetpars in sheets.items():
        if len(sheetpars)>0:
            failedtopopulate[sheetname] = sheetpars
    if len(failedtopopulate):
        errormsg = 'Not all parameters were successfully populated; missing parameters were:'
        errormsg += '\n%s' % failedtopopulate
        errormsg += versioncheck
        raise OptimaException(errormsg)
            
    return data




###########################################################################################################
## Define the workbook and parameter names -- should match makespreadsheet.py and partable in parameters.py
###########################################################################################################
        
def loadprogramspreadsheet(filename='testprogramdata.xlsx', verbose=2):
    '''
    Loads the spreadsheet (i.e. reads its contents into the data).
    Version: 1.0 (2016sep30)
    '''
    
    printv('Loading data from %s...' % filename, 1, verbose)
    sheets = odict()
    sheets['Populations & programs'] = ['programs'] # Data on program names and targeting
    sheets['Program data'] = odict()
    
    ## Basic setup
    data = odict() # Create structure for holding data
    data['meta'] = odict()
    data['meta']['date'] = today()
    data['meta']['sheets'] = sheets # Store parameter names
    try: 
        workbook = open_workbook(filename) # Open workbook
    except: 
        errormsg = 'Failed to load program spreadsheet: file "%s" not found or other problem' % filename
        raise OptimaException(errormsg)

    
    ## Calculate columns for which data are entered, and store the year ranges
    sheetdata = workbook.sheet_by_name('Program data') # Load this workbook
    lastdatacol, data['years'] = getyears(sheetdata)
    assumptioncol = lastdatacol + 1 # Figure out which column the assumptions are in; the "OR" space is in between
    
    ## Load program information
    sheetdata = workbook.sheet_by_name('Populations & programs') # Load 
    for row in range(sheetdata.nrows): 
        if sheetdata.cell_value(row,0)=='':
            thesedata = sheetdata.row_values(row, start_colx=2) # Data starts in 3rd column, finishes in 11th column
            if sheetdata.cell_value(row,1)=='':
                data['pops'] = thesedata[2:]
            else:
                progname = str(thesedata[0])
                data[progname] = odict()
                data[progname]['name'] = str(thesedata[1])
                data[progname]['targetpops'] = thesedata[2:]
                data[progname]['cost'] = []
                data[progname]['coverage'] = []
                data[progname]['unitcost'] = odict()
                data[progname]['saturation'] = odict()
    
    namemap = {'Total spend': 'cost',
               'Unit cost':'unitcost',
               'Coverage': 'coverage',
               'Saturation': 'saturation'} 
    sheetdata = workbook.sheet_by_name('Program data') # Load 
    
    for row in range(sheetdata.nrows): 
        sheetname = sheetdata.cell_value(row,0) # Sheet name
        progname = sheetdata.cell_value(row, 1) # Get the name of the program

        if sheetname == 'Program data': 
            printv('Loading "%s"...' % sheetname, 3, verbose)

        elif progname != '': # The first column is blank: it's time for the data
            thesedata = blank2nan(sheetdata.row_values(row, start_colx=3, end_colx=lastdatacol)) # Data starts in 3rd column, and ends lastdatacol-1
            assumptiondata = sheetdata.cell_value(row, assumptioncol)
            if assumptiondata != '': # There's an assumption entered
                thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
            if sheetdata.cell_value(row, 2) in namemap.keys(): # It's a regular variable without ranges
                thisvar = namemap[sheetdata.cell_value(row, 2)]  # Get the name of the indicator
                printv('Program: %s, indicator %s' % (progname, thisvar), 4, verbose)
                data[progname][thisvar] = thesedata # Store data
            else:
                thisvar = namemap[sheetdata.cell_value(row, 2).split(' - ')[0]]  # Get the name of the indicator
                thisestimate = sheetdata.cell_value(row, 2).split(' - ')[1]
                data[progname][thisvar][thisestimate] = thesedata # Store data
            checkblank = False if thisvar in ['unitcost', 'coverage', 'saturation'] else True # Don't check optional indicators, check everything else
            validatedata(thesedata, sheetname, thisvar, row, checkblank=checkblank)
            
    return data
