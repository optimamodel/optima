def loadspreadsheet(filename='test.xlsx', verbose=0):
    """
    Loads the spreadsheet (i.e. reads its contents into the data).
    This data sheet is used in the next step to update the corresponding model.
    
    Note: to add a new sheet, add it to the definition of "sheets" below, but also
    make sure it's being handled appropriately in the main loop.
    
    Version: 1.2 (2016jan19) by cliffk
    """
    
    ###########################################################################
    ## Preliminaries
    ###########################################################################
    
    from optima import OptimaException, odict, printv, today
    from numpy import nan, isnan, array, logical_or, nonzero, shape # For reading in empty values
    from xlrd import open_workbook # For opening Excel workbooks
    printv('Loading data from %s...' % filename, 1, verbose)
    
    
    def forcebool(entry, location=''):
        """ Convert an entry to be Boolean """
        if entry in [1, 'TRUE', 'true', 'True', 't', 'T']:
            return 1
        elif entry in [0, 'FALSE', 'false', 'False', 'f', 'F']:
            return 0
        else:
            errormsg = 'Boolean data "%s" not understood in spreadsheet location "%s"' % (entry, location)
            raise OptimaException(errormsg)
        
        
        
    
    def validatedata(thesedata, sheetname, thispar, row, checkupper=False, checkblank=True):
        ''' Do basic validation on the data: at least one point entered, between 0 and 1 or just above 0 if checkupper=False '''
        
        # Check that only numeric data have been entered
        for column,datum in enumerate(thesedata):
            if not isinstance(datum, (int, float)):
                errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
                errormsg += 'row=%i, column=%s, value="%s"\n' % (row+1, column, datum)
                errormsg += 'Be sure all entries are numeric'
                raise OptimaException(errormsg)
        
        # Now check integrity of data itself
        validdata = array(thesedata)[~isnan(thesedata)]
        if len(validdata):
            if checkupper: invalid = logical_or(array(validdata)>1, array(validdata)<0)
            else: invalid = array(validdata)<0
            if any(invalid):
                column = nonzero(invalid)[0]
                errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
                errormsg += 'row=%i, column(s)=%s, value(s)=%s\n' % (row+1, column, validdata)
                if checkupper: errormsg += 'Be sure that all values are >=0 and <=1'
                else: errormsg += 'Be sure that all values are >=0'
                raise OptimaException(errormsg)
        
        # No data entered
        elif checkblank:
            errormsg = 'No data or assumption entered for sheet "%s", parameter "%s", row=%i' % (sheetname, thispar, row) 
            raise OptimaException(errormsg)
        
        return None



    def blank2nan(thesedata):
        ''' Convert a blank entry to a nan '''
        return list(map(lambda val: nan if val=='' else val, thesedata))
        
    
    
    ###########################################################################################################
    ## Define the workbook and parameter names -- should match makespreadsheet.py and partable in parameters.py
    ###########################################################################################################
        
    sheets = odict()
    
    # Metadata -- population and program names -- array sizes are (# populations) and (# programs)
    sheets['Populations'] = ['pops']
    
    # Population size data -- array sizes are time x population x uncertainty
    sheets['Population size'] =  ['popsize']
    
    # HIV prevalence data -- array sizes are time x population x uncertainty
    sheets['HIV prevalence'] =  ['hivprev']
    
    # Time data -- array sizes are time x population
    sheets['Other epidemiology']  = ['death', 'stiprev', 'tbprev']
    sheets['Optional indicators'] = ['optnumtest', 'optnumdiag', 'optnuminfect', 'optprev', 'optplhiv', 'optdeath', 'optnewtreat']
    sheets['Testing & treatment'] = ['hivtest', 'aidstest', 'numtx', 'prep', 'numpmtct', 'birth', 'breast']
    sheets['Cascade']             = ['immediatecare', 'linktocare', 'numcare', 'pdhivcare', 'plhivcare', 'stoprate', 'leavecare', 'proploss', 'biofailure', 'successprop']
    sheets['Sexual behavior']     = ['numactsreg', 'numactscas', 'numactscom', 'condomreg', 'condomcas', 'condomcom', 'circum']
    sheets['Injecting behavior']  = ['numactsinj', 'sharing', 'numost']
    
    # Matrix data -- array sizes are population x population
    sheets['Partnerships & transitions'] = ['partreg','partcas','partcom','partinj','transit']
    
    # Constants -- array sizes are scalars x uncertainty
    sheets['Constants'] = [['transmfi', 'transmfr', 'transmmi', 'transmmr', 'transinj', 'mtctbreast', 'mtctnobreast'], 
                           ['cd4transacute', 'cd4transgt500', 'cd4transgt350', 'cd4transgt200', 'cd4transgt50', 'cd4translt50'],
                           ['progacute', 'proggt500', 'proggt350', 'proggt200', 'proggt50'],
                           ['recovgt500', 'recovgt350', 'recovgt200', 'recovgt50'],
                           ['deathacute', 'deathgt500', 'deathgt350', 'deathgt200', 'deathgt50', 'deathlt50', 'deathtreat', 'deathtb'],
                           ['effcondom', 'effcirc', 'effdx', 'effsti', 'effost', 'effpmtct', 'effprep','efftxunsupp', 'efftxsupp'],
                           ['disutilacute', 'disutilgt500', 'disutilgt350', 'disutilgt200', 'disutilgt50', 'disutillt50','disutiltx']]
    
    


    ###########################################################################
    ## Load data sheets
    ###########################################################################
    

    ## Basic setup
    data = odict() # Create sheetsure for holding data
    data['meta'] = odict()
    data['meta']['date'] = today()
    data['meta']['sheets'] = sheets # Store parameter names
    try: 
        workbook = open_workbook(filename) # Open workbook
    except: 
        errormsg = 'Failed to load spreadsheet: file "%s" not found or other problem' % filename
        raise OptimaException(errormsg)
    
    
    ## Calculate columns for which data are entered, and store the year ranges
    sheetdata = workbook.sheet_by_name('Population size') # Load this workbook
    data['years'] = [] # Initialize epidemiology data years
    for col in range(sheetdata.ncols):
        thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
        if thiscell=='' and len(data['years'])>0: #  We've gotten to the end
            lastdatacol = col # Store this column number
            break # Quit
        elif thiscell != '': # Nope, more years, keep going
            data['years'].append(float(thiscell)) # Add this year
    assumptioncol = lastdatacol + 1 # Figure out which column the assumptions are in; the "OR" space is in between
    
    ## Initialize populations
    data['pops'] = odict() # Initialize to empty list
    data['pops']['short'] = [] # Store short population/program names, e.g. "FSW"
    data['pops']['long'] = [] # Store long population/program names, e.g. "Female sex workers"
    data['pops']['male'] = [] # Store whether or not population is male
    data['pops']['female'] = [] # Store whether or not population is female
    data['pops']['age'] = [] # Store the age range for this population
    data['pops']['injects'] = [] # Store whether or not population injects
    data['pops']['sexworker'] = [] # Store whether or not population is commercial sex provider
    
    ## Initialize partnerships
    data['pships'] = odict() # Initialize to empty list
    data['pships']['reg'] = [] # Store regular partnerships
    data['pships']['cas'] = [] # Store casual partnerships
    data['pships']['com'] = [] # Store commercial partnerships
    data['pships']['inj'] = [] # Store injecting partnerships

    ## Initialize constants
    data['const'] = odict() # Initialize to empty list
    
    
    ##################################################################
    ## Now, actually load the data
    ##################################################################    
    
    ## Loop over each group of sheets
    for sheetname in sheets.keys(): # Loop over each type of data, but treat constants differently
        subparlist = sheets[sheetname] # List of subparameters
        sheetdata = workbook.sheet_by_name(sheetname) # Load this workbook
        parcount = -1 # Initialize the parameter count
        printv('Loading "%s"...' % sheetname, 2, verbose)
        
        # Loop over each row in the workbook, starting from the top
        for row in range(sheetdata.nrows): 
            paramcategory = sheetdata.cell_value(row,0) # See what's in the first column for this row
            subparam = sheetdata.cell_value(row, 1) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
            
            if paramcategory != '': # It's not blank: e.g. "HIV prevalence"
                printv('Loading "%s"...' % paramcategory, 3, verbose)
                parcount += 1 # Increment the parameter count
                
                # It's anything other than the populations or constants sheet: create an empty list
                if sheetname not in ['Populations', 'Constants']: 
                    try:
                        thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'popsize'
                    except:
                        errormsg = 'Incorrect number of headings found for sheet "%s"\n' % sheetname
                        errormsg += 'Check that there is no extra text in the first two columns'
                        raise OptimaException(errormsg)
                    data[thispar] = [] # Initialize to empty list
            
            elif subparam != '': # The first column is blank: it's time for the data
                printv('Parameter: %s' % subparam, 4, verbose)
                
                
                # It's pops-data, split into pieces
                if sheetname=='Populations': 
                    thesedata = sheetdata.row_values(row, start_colx=2, end_colx=11) # Data starts in 3rd column, finishes in 11th column
                    data['pops']['short'].append(str(thesedata[0]))
                    data['pops']['long'].append(str(thesedata[1]))
                    data['pops']['male'].append(forcebool(thesedata[2], 'male, row %i'% row))
                    data['pops']['female'].append(forcebool(thesedata[3], 'female, row %i'% row))
                    data['pops']['age'].append([int(thesedata[4]), int(thesedata[5])])
                    data['pops']['injects'].append(forcebool(thesedata[6], 'injects, row %i'% row))
                    data['pops']['sexworker'].append(forcebool(thesedata[7], 'sexworker, row %i'% row))
                    
                
                # It's key data, save both the values and uncertainties
                elif sheetname in ['Population size', 'HIV prevalence']:
                    if len(data[thispar])==0: 
                        data[thispar] = [[] for z in range(3)] # Create new variable for best, low, high
                    thesedata = blank2nan(sheetdata.row_values(row, start_colx=3, end_colx=lastdatacol)) # Data starts in 4th column -- need room for high/best/low
                    assumptiondata = sheetdata.cell_value(row, assumptioncol)
                    if assumptiondata != '': thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                    blhindices = {'best':0, 'low':1, 'high':2} # Define best-low-high indices
                    blh = sheetdata.cell_value(row, 2) # Read in whether indicator is best, low, or high
                    data[thispar][blhindices[blh]].append(thesedata) # Actually append the data
                    validatedata(thesedata, sheetname, thispar, row, checkblank=False)
                    if thispar=='hivprev':
                       validatedata(thesedata, sheetname, thispar, row, checkupper=True, checkblank=False)

                    
                
                # It's basic data, append the data and check for programs
                elif sheetname in ['Other epidemiology', 'Optional indicators', 'Testing & treatment', 'Cascade', 'Sexual behavior', 'Injecting behavior']: 
                    thesedata = blank2nan(sheetdata.row_values(row, start_colx=2, end_colx=lastdatacol-1)) # Data starts in 3rd column, and ends lastdatacol-1
                    assumptiondata = sheetdata.cell_value(row, assumptioncol-1)
                    if assumptiondata != '': # There's an assumption entered
                        thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                    data[thispar].append(thesedata) # Store data
                    checkblank = False if sheetname=='Optional indicators' else True # Don't check optional indicators, check everything else
                    validatedata(thesedata, sheetname, thispar, row, checkblank=checkblank)
                    if thispar in ['stiprev', 'tbprev', 'hivtest', 'aidstest', 'prep', 'condomreg', 'condomcas', 'condomcom', 'circum',  'sharing']: # All probabilities
                        validatedata(thesedata, sheetname, thispar, row, checkupper=True)                        



                # It's a matrix, append the data                                     
                elif sheetname in ['Partnerships & transitions']:
                    thesedata = sheetdata.row_values(row, start_colx=2, end_colx=sheetdata.ncols) # Data starts in 3rd column
                    thesedata = list(map(lambda val: 0 if val=='' else val, thesedata)) # Replace blanks with 0
                    data[thispar].append(thesedata) # Store data
                    validatedata(thesedata, sheetname, thispar, row)
                
                
                
                # It's a constant, create a new dictionary entry
                elif sheetname in ['Constants']:
                    thesedata = blank2nan(sheetdata.row_values(row, start_colx=2, end_colx=5)) # Data starts in 3rd column, finishes in 5th column
                    try:
                        subpar = subparlist[parcount].pop(0) # Pop first entry of subparameter list, which is namelist[parcount][1]
                    except:
                        errormsg = 'Failed to load constant subparameter from subparlist %i' % parcount
                        raise OptimaException(errormsg)
                    validatedata(thesedata, sheetname, thispar, row)
                    data['const'][subpar] = thesedata # Store data
                
                # It's not recognized: throw an error
                else: 
                    errormsg = 'Sheet name "%s" not recognized: please do not change the names of the sheets!' % sheetname
                    raise OptimaException(errormsg)
    
    
    # Check that matrices have correct shape
    data['npops'] = len(data['pops']['short'])
    for key in sheets['Partnerships & transitions']:
        thesedata = data[key]
        matrixshape = shape(array(thesedata))
        if matrixshape[0] != data['npops'] or matrixshape[1] != data['npops']:
            errormsg = 'Matrix "%s" in partnerships & transitions sheet is not square\n' % key
            errormsg += '(rows = %i, columns = %i, should be %i)\n' % (matrixshape[0], matrixshape[1], data['npops'])
            errormsg += 'Check for missing rows or added text'
            raise OptimaException(errormsg)
    
    
    # Store tuples of partnerships
    for row in range(data['npops']):
        for col in range(data['npops']):
            if data['partreg'][row][col]:
                data['pships']['reg'].append((data['pops']['short'][row],data['pops']['short'][col]))
            if data['partcas'][row][col]:
                data['pships']['cas'].append((data['pops']['short'][row],data['pops']['short'][col]))
            if data['partcom'][row][col]:
                data['pships']['com'].append((data['pops']['short'][row],data['pops']['short'][col]))
            if data['partinj'][row][col]:
                data['pships']['inj'].append((data['pops']['short'][row],data['pops']['short'][col]))
    

    printv('...done loading data.', 2, verbose)
    return data


#loadspreadsheet('test.xlsx') # Uncomment for debugging
