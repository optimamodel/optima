def loadspreadsheet(filename='test.xlsx', verbose=0):
    """
    Loads the spreadsheet (i.e. reads its contents into the data sheetsure).
    This data sheetsure is used in the next step to update the corresponding model.
    
    Version: 2015oct31
    """
    
    ###########################################################################
    ## Preliminaries
    ###########################################################################
    
    from utils import printv
    from numpy import nan, isnan, array, logical_or, nonzero # For reading in empty values
    from xlrd import open_workbook # For opening Excel workbooks
    from time import strftime # For determining when a spreadsheet was last uploaded
    printv('Loading data from %s...' % filename, 1, verbose)
    
    
    def forcebool(entry):
        """ Convert an entry to be Boolean """
        if entry in [1, 'TRUE', 'true', 'True', 't', 'T']:
            return 1
        elif entry in [0, 'FALSE', 'false', 'False', 'f', 'F']:
            return 0
        else:
            raise Exception('Boolean data supposed to be entered, but not understood (%s)' % entry)
        
    
    def validatedata(thesedata, sheetname, thispar, row, column):
        validdata = array(thesedata)[~isnan(thesedata)]
        if len(validdata):
            invalid = logical_or(array(validdata)>1, array(validdata)<0)
            if any(invalid):
                column = nonzero(invalid)[0]
                raise Exception('Invalid entry in spreadsheet "%s": parameter %s (row=%i, column(s)=%s, value=%f)' % (thispar, sheetname, row+1, column, thesedata[column[0]]))


        
    ###########################################################################
    ## Define the workbook and parameter names
    ###########################################################################
        
    sheets = dict()
    
    # Define group names explicitly so as keep order -- defined here, just below, in test.xlsx, and in makespreadsheet()
    sheetnames = [
    'Populations',
    'Population size',
    'HIV prevalence',
    'Other epidemiology',
    'Optional indicators',
    'Testing & treatment',
    'Sexual behavior',
    'Injecting behavior',
    'Partnerships',
    'Transitions',
    'Constants',
    'Economics and costs']
    
    # Metadata -- population and program names -- array sizes are (# populations) and (# programs)
    sheets['Populations'] = ['pops']
    
    # Population size data -- array sizes are time x population x uncertainty
    sheets['Population size'] =  ['popsize']
    
    # HIV prevalence data -- array sizes are time x population x uncertainty
    sheets['HIV prevalence'] =  ['hivprev']
    
    # Time data -- array sizes are time x population
    sheets['Other epidemiology']  = ['death', 'stiprev', 'tbprev']
    sheets['Optional indicators'] = ['optnumtest', 'optnumdiag', 'optnuminfect', 'optprev', 'optdeath', 'optnewtreat']
    sheets['Testing & treatment'] = ['hivtest', 'aidstest', 'numfirstline', 'numsecondline', 'txelig', 'prep', 'numpmtct', 'birth', 'breast']
    sheets['Sexual behavior']     = ['numactsreg', 'numactscas', 'numactscom', 'condomreg', 'condomcas', 'condomcom', 'circum']
    sheets['Injecting behavior']  = ['numinject', 'sharing', 'numost']
    
    # Matrix data -- array sizes are population x population
    sheets['Partnerships'] = ['partreg','partcas','partcom','partinj']
    sheets['Transitions']  = ['transasym','transsym']
    
    # Constants -- array sizes are scalars x uncertainty
    sheets['Constants'] = [['transmfi', 'transmfr', 'transmmi', 'transmmr', 'transinj', 'mtctbreast', 'mtctnobreast'], \
                           ['cd4transacute', 'cd4transgt500', 'cd4transgt350', 'cd4transgt200', 'cd4transgt50', 'cd4transaids'], \
                           ['progacute', 'proggt500', 'proggt350', 'proggt200', 'proggt50'],\
                           ['recovgt500', 'recovgt350', 'recovgt200', 'recovgt50', 'recovaids'],\
                           ['fail'],\
                           ['deathacute', 'deathgt500', 'deathgt350', 'deathgt200', 'deathgt50', 'deathaids', 'deathtreat', 'deathtb'],\
                           ['effcondom', 'effcirc', 'effdx', 'effsti', 'effdis', 'effost', 'effpmtct', 'efftx', 'effprep'],\
                           ['disutilacute', 'disutilgt500', 'disutilgt350', 'disutilgt200', 'disutilgt50', 'disutilaids','disutiltx']]
    

    


    ###########################################################################
    ## Load data sheets
    ###########################################################################
    

    ## Basic setup
    data = dict() # Create sheetsure for holding data
    data['date'] = strftime("%Y-%m-%d %H:%M:%S")
    try: workbook = open_workbook(filename) # Open workbook
    except: raise Exception('Failed to load spreadsheet: file "%s" not found or other problem' % filename)
    
    ## Loop over each group of sheets
    for sheetname in sheetnames: # Loop over each type of data, but treat constants differently
        lastdatacol = None
        subparlist = sheets[sheetname] # List of subparameters
        sheetdata = workbook.sheet_by_name(sheetname) # Load this workbook
        parcount = -1 # Initialize the parameter count
        printv('  Loading "%s"...' % sheetname, 2, verbose)
        
        ## Calculate columns for which data are entered, and store the year ranges
        if sheetname == 'Population size': # Need to gather year ranges for epidemic etc. data
            data['years'] = [] # Initialize epidemiology data years
            for col in range(sheetdata.ncols):
                thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
                if thiscell=='' and len(data['years'])>0: #  We've gotten to the end
                    lastdatacol = col # Store this column number
                    break # Quit
                elif thiscell != '': # Nope, more years, keep going
                    data['years'].append(float(thiscell)) # Add this year
        
        ## Figure out which column the assumptions are in
        if lastdatacol:  
            assumptioncol = lastdatacol + 1 # The "OR" space is in between
        
        
        
        
        ##################################################################
        ## Now, actually load the data
        ##################################################################
        
        
        # Loop over each row in the workbook, starting from the top
        for row in range(sheetdata.nrows): 
            paramcategory = sheetdata.cell_value(row,0) # See what's in the first column for this row
            
            if paramcategory != '': # It's not blank: e.g. "HIV prevalence"
                printv('Loading "%s"...' % paramcategory, 3, verbose)
                parcount += 1 # Increment the parameter count
                
                # It's popdata: pull out each of the pieces
                if sheetname=='Populations': 
                    thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'popsize'
                    data['pops'] = dict() # Initialize to empty list
                    data['pops']['short'] = [] # Store short population/program names, e.g. "FSW"
                    data['pops']['long'] = [] # Store long population/program names, e.g. "Female sex workers"
                    data['pops']['male'] = [] # Store whether or not this population is male
                    data['pops']['female'] = [] # Store whether or not this population is female
                    data['pops']['injects'] = [] # Store whether or not this population injects drugs
                    data['pops']['sexmen'] = [] # Store whether or not this population has sex with men
                    data['pops']['sexwomen'] = [] # Store whether or not this population has sex with women
                    data['pops']['sexworker'] = [] # Store whether or not this population is a sex worker
                    data['pops']['client'] = [] # Store whether or not this population is a client of sex workers
                
                # It's anything else: create an empty list
                else: 
                    thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'popsize'
                    data[thispar] = [] # Initialize to empty list
            
            
            if paramcategory == '': # The first column is blank: it's time for the data
                subparam = sheetdata.cell_value(row, 1) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
                
                if subparam != '': # The subparameter name isn't blank, load something!
                    printv('Parameter: %s' % subparam, 4, verbose)
                    
                    
                    # It's pops-data, split into pieces
                    if sheetname=='Populations': 
                        thesedata = sheetdata.row_values(row, start_colx=2, end_colx=11) # Data starts in 3rd column, finishes in 11th column
                        data['pops']['short'].append(thesedata[0])
                        data['pops']['long'].append(thesedata[1])
                        data['pops']['male'].append(forcebool(thesedata[2]))
                        data['pops']['female'].append(forcebool(thesedata[3]))
                        data['pops']['injects'].append(forcebool(thesedata[4]))
                        data['pops']['sexmen'].append(forcebool(thesedata[5]))
                        data['pops']['sexwomen'].append(forcebool(thesedata[6]))
                        data['pops']['sexworker'].append(forcebool(thesedata[7]))
                        data['pops']['client'].append(forcebool(thesedata[8]))

                    
                    # It's key data, save both the values and uncertainties
                    if sheetname in ['Population size', 'HIV prevalence']:
                        if len(data[thispar])==0: 
                            data[thispar] = [[] for z in range(3)] # Create new variable for best, low, high
                        thesedata = sheetdata.row_values(row, start_colx=3, end_colx=lastdatacol) # Data starts in 4th column
                        thesedata = list(map(lambda val: nan if val=='' else val, thesedata)) # Replace blanks with nan
                        assumptiondata = sheetdata.cell_value(row, assumptioncol)
                        if assumptiondata != '': thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                        blhindices = {'best':0, 'low':1, 'high':2} # Define best-low-high indices
                        blh = sheetdata.cell_value(row, 2) # Read in whether indicator is best, low, or high
                        data[thispar][blhindices[blh]].append(thesedata) # Actually append the data
                        if thispar=='hivprev':
                            validatedata(thesedata, sheetname, thispar, row)
                        
                    
                    # It's basic data, append the data and check for programs
                    if sheetname in ['Other epidemiology', 'Optional indicators', 'Testing & treatment', 'Sexual behavior', 'Injecting behavior']: 
                        thesedata = sheetdata.row_values(row, start_colx=2, end_colx=lastdatacol) # Data starts in 3rd column
                        thesedata = list(map(lambda val: nan if val=='' else val, thesedata)) # Replace blanks with nan
                        assumptiondata = sheetdata.cell_value(row, assumptioncol)
                        if assumptiondata != '': # There's an assumption entered
                            thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                        data[thispar].append(thesedata) # Store data
                        if thispar in ['stiprev', 'tbprev', 'hivtest', 'aidstest', 'prep', 'condomreg', 'condomcas', 'condomcom', 'circum',  'sharing']: # All probabilities
                            validatedata(thesedata, sheetname, thispar, row)                        


                    # It's a matrix, append the data                                     
                    elif sheetname=='matrices':
                        thesedata = sheetdata.row_values(row, start_colx=2, end_colx=sheetdata.ncols) # Data starts in 3rd column
                        thesedata = list(map(lambda val: 0 if val=='' else val, thesedata)) # Replace blanks with 0
                        data[thispar].append(thesedata) # Store data
                    
                    
                    # It's a constant, create a new dictionary entry
                    elif sheetname=='constants':
                        thesedata = sheetdata.row_values(row, start_colx=2, end_colx=5) # Data starts in 3rd column, finishes in 5th column
                        thesedata = list(map(lambda val: nan if val=='' else val, thesedata)) # Replace blanks with nan
                        subpar = subparlist[parcount][1].pop(0) # Pop first entry of subparameter list, which is namelist[parcount][1]
                        data[thispar][subpar] = thesedata # Store data
    
    
    
    
    printv('...done loading data.', 2, verbose)
    return data
