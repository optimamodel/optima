def loadspreadsheet(filename='example.xlsx',verbose=2):
    """
    Loads the spreadsheet (i.e. reads its contents into the data structure).
    This data structure is used in the next step to update the corresponding model.
    The spreadsheet is assumed to be in the format specified in example.xlsx.
    """

    ###########################################################################
    ## Preliminaries
    ###########################################################################
    
    if verbose>=1: print('Loading data from %s...' % filename)
    from matplotlib.pylab import nan, array # For reading in empty values
    from xlrd import open_workbook # For opening Excel spreadsheets
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    
    
    ###########################################################################
    ## Define the spreadsheet and parameter names
    ###########################################################################
    
    # Metadata -- population and program names -- array sizes are (# populations) and (# programs)
    metadata = [['Populations & programs', 'meta', ['pops', 'progs']]]
    
    # Key data -- array sizes are time x population x uncertainty
    keydata =  [['Demographics & HIV prevalence', 'key', ['popsize', 'hivprev']]]
    
    # Time data -- array sizes are time x population
    timedata = [
                 ['Cost & coverage',     'costcov', ['cost', 'cov']], \
                 ['Other prevalences',   'epi',     ['stiprevulc', 'stiprevdis', 'tbprev']], \
                 ['Optional indicators', 'opt',     ['stiprevulc', 'stiprevdis', 'tbprev']], \
                 ['Testing & treatment', 'txrx',    ['testrate', 'aidstestrate', 'numtests', 'numdiagnoses', 'numinfections', 'numdeaths', 'numfirstline', 'numsecondline', 'numpmtct','numbreastpmtct']], \
                 ['Sexual behavior',     'sex',     ['numactsreg', 'numactscas', 'numactscom', 'condomreg', 'condomcas', 'condomcom', 'circum']], \
                 ['Injecting behavior',  'drug',    ['numinject', 'sharing', 'ost']], \
                 ['Macroeconomics',      'macro',   ['gdp', 'revenue', 'totalexpend', 'totalhealth', 'domestichealth']]
                ]
                 
    # Matrix data -- array sizes are population x population
    matrices = [
                ['Partnerships', 'pships',  ['reg','cas','com','drug']], \
                ['Transitions',  'transit', ['asym','sym']]
               ]
    
    # Constants -- array sizes are scalars x uncertainty
    constants = [
                 ['Constants', 'const',              [['trans',    ['mfi','mfr','mmi','mmr','inj','mtct']], \
                                                      ['cd4trans', ['acute','gt500','gt350','gt200','aids']], \
                                                      ['prog',     ['acute','gt500','gt350','gt200']],\
                                                      ['recov',    ['gt500','gt350','gt200','aids']],\
                                                      ['fail',     ['first','second']],\
                                                      ['death',    ['background','inj','acute','gt500','gt350','gt200','aids','treat','tb']],\
                                                      ['eff',      ['condom','circ','dx','sti','meth','pmtct','tx']]]], \
                 ['Disutilities & costs', 'cost',    [['disutil',  ['acute','gt500','gt350','gt200','aids','tx']], \
                                                      ['health',    ['acute','gt500','gt350','gt200','aids']], \
                                                      ['social',    ['acute','gt500','gt350','gt200','aids']]]]
                ]
    
    sheetstructure = [metadata, keydata, timedata, matrices, constants] 
    print('WARNING should change this to have read-in directly based on each class')
    


    ###########################################################################
    ## Load data sheets
    ###########################################################################
    
    data = struct() # Create structure for holding data
    data.__doc__ = 'Raw data as loaded from the spreadsheet, including both epidemiological and behavioral data, plus economics and velociraptors.'
    programs = struct() # Create structure for holding program data
    programs.__doc__ = 'Parameters that define the HIV programs -- cost-coverage and coverage-outcome curves.'
    spreadsheet = open_workbook(filename) # Open spreadsheet

    for sheetclass in sheetstructure: # Loop over each type of data, but treat constants differently
        for sheet in sheetclass: # Loop over each spreadsheet for that data -- just one for constants
            sheetname = sheet[0] # Name of the spreadsheet
            name = sheet[1] # Pull out the name of this field, e.g. 'epi'
            subparlist = sheet[2] # List of subparameters
            if verbose>=2: print('  Loading "%s"...' % sheetname)
            
            
            data[name] = struct() # Create structure for holding data, e.g. data.epi
            sheetdata = spreadsheet.sheet_by_name(sheetname) # Load this spreadsheet
            parcount = -1 # Initialize the parameter count
            
            if sheetname=='Demographics & HIV prevalence': # Initialize row counts by using the first sheet that uses year ranges
                lastdatacol = sheetdata.ncols - 8 # The 8 makes sense...
                assumptioncol = lastdatacol + 1 # The "OR" space is in between
                programcols = assumptioncol + array([3,5,7]) # Sorry for the weird numbering...not sure what the deal is
            
            
            # Loop over each row in the spreadsheet
            for row in range(sheetdata.nrows): 
                paramcategory = sheetdata.cell_value(row,0) # See what's in the first column for this row
                
                if not(paramcategory==''): # It's not blank: e.g. "HIV prevalence"
                    if verbose>=2: print('    Loading "%s"...' % paramcategory)
                    parcount += 1 # Increment the parameter count
                    
                    if name=='meta': # Metadata
                        thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'pop'
                        data[name][thispar] = struct() # Initialize to empty list
                        data[name][thispar].short = [] # Store short population/program names, e.g. "FSW"
                        data[name][thispar].long = [] # Store long population/program names, e.g. "Female sex workers"
                    
                    elif name=='const' or name=='cost': # It's a constant or a cost: create a structure
                        thispar = subparlist[parcount][0] # Get the name of this parameter, e.g. 'trans'
                        data[name][thispar] = struct() # Need yet another structure if it's a constant!
                        
                    else: # It's basic data or a matrix: create an empty list
                        thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'popsize'                    
                        data[name][thispar] = [] # Initialize to empty list

                
                if paramcategory=='': # The first column is blank: it's time for the data
                    subparam = sheetdata.cell_value(row, 1) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
                    
                    if not(subparam==''): # The subparameter name isn't blank, load something!
                        if verbose >=3: print("      Parameter: subparam" % subparam)
                        
                        # It's meta-data, split into pieces
                        if name=='meta': 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=6) # Data starts in 3rd column, finishes in 6th column
                            data[name][thispar].short.append(thesedata[0])
                            data[name][thispar].long.append(thesedata[1])
                        
                        # It's basic data, append the data and check for programs
                        if sheettype==1: 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=lastcol) # Data starts in 3rd column, finishes in 21st column
                            thesedata = map(lambda val: nan if val=='' else val, thesedata) # Replace blanks with nan
                            assumptiondata = sheetdata.cell_value(row, assumptioncol)
                            if not(assumptiondata==''): thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                            data[name][thispar].append(thesedata) # Store data
                            
                            # Load program data -- only exists for basic data
                            programname = str(sheetdata.cell_value(row, programcols[0])) # Convert to plain string since otherwise can't be used as a dict key
                            if not(programname==''): # Not blank: a program exists!
                                if not(programs.has_key(programname)): programs[programname] = [] # Create new list if none exists
                                outcomes = sheetdata.row_values(row, start_colx=programcols[1], end_colx=programcols[2]) # Get outcome data
                                programs[programname].append([[name,thispar], outcomes]) # Append to program
                        
                        # It's a matrix, append the data                                     
                        elif name=='pships' or name=='transit':
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=sheetdata.ncols) # Data starts in 3rd column
                            thesedata = map(lambda val: 0 if val=='' else val, thesedata) # Replace blanks with nan
                            data[name][thispar].append(thesedata) # Store data
                        
                        # It's a constant, create a new dictionary entry
                        elif name=='const' or name=='cost':
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=5) # Data starts in 3rd column, finishes in 5th column
                            thesedata = map(lambda val: 0 if val=='' else val, thesedata) # Replace blanks with nan
                            subpar = subparlist[parcount][1].pop(0) # Pop first entry of subparameter list, which is namelist[parcount][1]
                            data[name][thispar][subpar] = thesedata # Store data
    
    if verbose>=2: print('  ...done loading data.')
    return data, programs
