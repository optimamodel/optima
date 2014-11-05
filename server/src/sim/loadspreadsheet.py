def loadspreadsheet(filename='example.xlsx',verbose=2):
    """
    Loads the spreadsheet (i.e. reads its contents into the data structure).
    This data structure is used in the next step to update the corresponding model.
    The spreadsheet is assumed to be in the format specified in example.xlsx.
    
    Version: 2014nov05
    """

    ###########################################################################
    ## Preliminaries
    ###########################################################################
    
    from printv import printv
    from matplotlib.pylab import nan, array # For reading in empty values
    from xlrd import open_workbook # For opening Excel spreadsheets
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    printv('Loading data from %s...' % filename, 1, verbose)
    
    ###########################################################################
    ## Define the spreadsheet and parameter names
    ###########################################################################
    
    # Metadata -- population and program names -- array sizes are (# populations) and (# programs)
    metadata = [['Populations & programs', 'meta', ['pops', 'progs']]]
    
    # Key data -- array sizes are time x population x uncertainty
    keydata =  [['Demographics & HIV prevalence', 'key', ['popsize', 'hivprev']]]
    
    # Time data -- array sizes are time x population
    timedata = [
                 ['Cost & coverage',     'costcov', ['cov', 'total', 'unit']], \
                 ['Other epidemiology',  'epi',     ['death', 'stiprevulc', 'stiprevdis', 'tbprev']], \
                 ['Optional indicators', 'opt',     ['numtest', 'numdiag', 'numinfect', 'prev', 'death', 'newtreat']], \
                 ['Testing & treatment', 'txrx',    ['testrate', 'aidstestrate', 'numfirstline', 'numsecondline', 'numpmtct', 'birth', 'breast']], \
                 ['Sexual behavior',     'sex',     ['numactsreg', 'numactscas', 'numactscom', 'condomreg', 'condomcas', 'condomcom', 'circum']], \
                 ['Injecting behavior',  'inj',     ['numinject', 'sharing', 'ost']], \
                 ['Macroeconomics',      'macro',   ['gdp', 'revenue', 'govtexpend', 'totalhealth', 'domestichealth', 'domestichiv', 'globalfund', 'pepfar', 'otherint', 'private']]
                ]
                 
    # Matrix data -- array sizes are population x population
    matrices = [
                ['Partnerships', 'pships',  ['reg','cas','com','inj']], \
                ['Transitions',  'transit', ['asym','sym']]
               ]
    
    # Constants -- array sizes are scalars x uncertainty
    constants = [
                 ['Constants', 'const',              [['trans',    ['mfi', 'mfr', 'mmi', 'mmr', 'inj', 'mtctbreast', 'mtctnobreast']], \
                                                      ['cd4trans', ['acute','gt500','gt350','gt200','aids']], \
                                                      ['prog',     ['acute','gt500','gt350','gt200']],\
                                                      ['recov',    ['gt500','gt350','gt200','aids']],\
                                                      ['fail',     ['first','second']],\
                                                      ['death',    ['acute','gt500','gt350','gt200','aids','treat','tb']],\
                                                      ['eff',      ['condom','circ','dx','sti','meth','pmtct','tx']]]], \
                 ['Disutilities & costs', 'cost',    [['disutil',  ['acute','gt500','gt350','gt200','aids','tx']], \
                                                      ['health',   ['acute','gt500','gt350','gt200','aids']], \
                                                      ['social',   ['acute','gt500','gt350','gt200','aids']]]]
                ]
    
    
    ## Ugly, but allow the list of groups to be used as name and also as variables
    sheetstructure = struct()
    sheetstructure.metadata = metadata
    sheetstructure.keydata = keydata
    sheetstructure.timedata = timedata
    sheetstructure.matrices = matrices
    sheetstructure.constants = constants
    


    ###########################################################################
    ## Load data sheets
    ###########################################################################
    
    
    ## Basic setup
    data = struct() # Create structure for holding data
    data.__doc__ = 'Raw data as loaded from the spreadsheet, including both epidemiological and behavioral data, plus economics and velociraptors.'
    programs = struct() # Create structure for holding program data
    programs.__doc__ = 'Parameters that define the HIV programs -- cost-coverage and coverage-outcome curves.'
    spreadsheet = open_workbook(filename) # Open spreadsheet
    
    
    ## Loop over each group of sheets
    for groupname in sheetstructure.keys(): # Loop over each type of data, but treat constants differently
        sheetgroup = sheetstructure[groupname]
        for sheet in sheetgroup: # Loop over each spreadsheet for that data -- just one for constants
            sheetname = sheet[0] # Name of the spreadsheet
            name = sheet[1] # Pull out the name of this field, e.g. 'epi'
            subparlist = sheet[2] # List of subparameters
            data[name] = struct() # Create structure for holding data, e.g. data.epi
            sheetdata = spreadsheet.sheet_by_name(sheetname) # Load this spreadsheet
            parcount = -1 # Initialize the parameter count
            printv('  Loading "%s"...' % sheetname, 2, verbose)
            
            
            ## Calculate columns for which data are entered, and store the year ranges
            if groupname == 'keydata' or (groupname == 'timedata' and name != 'macro'): # Need to gather year ranges for epidemic etc. data
                data.epiyears = [] # Initialize epidemiology data years
                for col in range(sheetdata.ncols):
                    thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
                    if thiscell=='' and len(data.epiyears)>0: #  We've gotten to the end
                        lastdatacol = col # Store this column number
                        break # Quit
                    elif thiscell != '': # Nope, more years, keep going
                        data.epiyears.append(float(thiscell)) # Add this year
            
            if name == 'macro': # Need to gather year ranges for economic data
                data.econyears = [] # Initialize epidemiology data years
                for col in range(sheetdata.ncols):
                    thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
                    if thiscell=='' and len(data.econyears)>0: #  We've gotten to the end
                        lastdatacol = col # Store this column number
                        break # Quit
                    elif thiscell != '': # Nope, more years, keep going
                        data.econyears.append(float(thiscell)) # Add this year
                
            assumptioncol = lastdatacol + 1 # The "OR" space is in between
            programcols = assumptioncol + array([3,5,6,8,9]) # Sorry for the weird numbering...not sure what the deal is
            
            
            
            
            ##################################################################
            ## Now, actually load the data
            ##################################################################
            
            
            # Loop over each row in the spreadsheet
            for row in range(sheetdata.nrows): 
                paramcategory = sheetdata.cell_value(row,0) # See what's in the first column for this row
                
                
                if paramcategory != '': # It's not blank: e.g. "HIV prevalence"
                    printv('Loading "%s"...' % paramcategory, 3, verbose)
                    parcount += 1 # Increment the parameter count
                    
                    if groupname=='metadata': # Metadata
                        thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'pop'
                        data[name][thispar] = struct() # Initialize to empty list
                        data[name][thispar].short = [] # Store short population/program names, e.g. "FSW"
                        data[name][thispar].long = [] # Store long population/program names, e.g. "Female sex workers"

                    elif groupname=='keydata' or groupname=='timedata' or groupname=='matrices': # It's basic data or a matrix: create an empty list
                        thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'popsize'                    
                        data[name][thispar] = [] # Initialize to empty list
    
                    elif groupname=='constants': # It's a constant or a cost: create a structure
                        thispar = subparlist[parcount][0] # Get the name of this parameter, e.g. 'trans'
                        data[name][thispar] = struct() # Need yet another structure if it's a constant!
                    
                    else:
                        raise Exception('Group name %s not recognized!' % groupname)
                        

                
                if paramcategory == '': # The first column is blank: it's time for the data
                    subparam = sheetdata.cell_value(row, 1) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
                    
                    if subparam != '': # The subparameter name isn't blank, load something!
                        printv('Parameter: %s' % subparam, 4, verbose)
                        
                        # It's meta-data, split into pieces
                        if groupname=='metadata': 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=6) # Data starts in 3rd column, finishes in 6th column
                            data[name][thispar].short.append(thesedata[0])
                            data[name][thispar].long.append(thesedata[1])
                        
                        # It's key data, save both the values and uncertainties
                        if groupname=='keydata':
                            if len(data[name][thispar])==0: 
                                data[name][thispar] = [[] for z in range(3)] # Create new variable for best, low, high
                            thesedata = sheetdata.row_values(row, start_colx=3, end_colx=lastdatacol) # Data starts in 4th column
                            thesedata = map(lambda val: nan if val=='' else val, thesedata) # Replace blanks with nan
                            assumptiondata = sheetdata.cell_value(row, assumptioncol)
                            if assumptiondata != '': thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                            blhindices = {'best':0, 'low':1, 'high':2} # Define best-low-high indices
                            blh = sheetdata.cell_value(row, 2) # Read in whether indicator is best, low, or high
                            data[name][thispar][blhindices[blh]].append(thesedata) # Actually append the data
                            
                        
                        # It's basic data, append the data and check for programs
                        if groupname=='timedata': 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=lastdatacol) # Data starts in 3rd column
                            thesedata = map(lambda val: nan if val=='' else val, thesedata) # Replace blanks with nan
                            assumptiondata = sheetdata.cell_value(row, assumptioncol)
                            if assumptiondata != '': thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                            data[name][thispar].append(thesedata) # Store data
                            
                            # Load program data -- only exists for time data
                            if sheetdata.ncols>=programcols[-1]: # Don't try to read more data than exist
                                programname = str(sheetdata.cell_value(row, programcols[0])) # Convert to plain string since otherwise can't be used as a dict key
                                if programname != '': # Not blank: a program exists!
                                    if not(programs.has_key(programname)): programs[programname] = [] # Create new list if none exists
                                    zerocov = sheetdata.row_values(row, start_colx=programcols[1], end_colx=programcols[2]+1) # Get outcome data
                                    fullcov = sheetdata.row_values(row, start_colx=programcols[3], end_colx=programcols[4]+1) # Get outcome data
                                    programs[programname].append([[name,thispar], [zerocov, fullcov]]) # Append to program
                        
                        
                        # It's a matrix, append the data                                     
                        elif groupname=='matrices':
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=sheetdata.ncols) # Data starts in 3rd column
                            thesedata = map(lambda val: 0 if val=='' else val, thesedata) # Replace blanks with 0
                            data[name][thispar].append(thesedata) # Store data
                        
                        # It's a constant, create a new dictionary entry
                        elif name=='const' or name=='cost':
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=5) # Data starts in 3rd column, finishes in 5th column
                            thesedata = map(lambda val: nan if val=='' else val, thesedata) # Replace blanks with nan
                            subpar = subparlist[parcount][1].pop(0) # Pop first entry of subparameter list, which is namelist[parcount][1]
                            data[name][thispar][subpar] = thesedata # Store data
    
    printv('...done loading data.', 2, verbose)
    return data, programs