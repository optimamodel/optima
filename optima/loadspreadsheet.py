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
        

        
    ###########################################################################
    ## Define the workbook and parameter names
    ###########################################################################
        
    sheets = dict()
    
    # Define group names explicitly so keep order
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
    sheets['Other epidemiology']  = ['death', 'stiprevulc', 'stiprevdis', 'tbprev']
    sheets['Optional indicators'] = ['numtest', 'numdiag', 'numinfect', 'prev', 'death', 'newtreat']
    sheets['Testing & treatment'] = ['hivtest', 'aidstest', 'numfirstline', 'numsecondline', 'txelig', 'prep', 'numpmtct', 'birth', 'breast']
    sheets['Sexual behavior']     = ['numactsreg', 'numactscas', 'numactscom', 'condomreg', 'condomcas', 'condomcom', 'circum']
    sheets['Injecting behavior']  = ['numinject', 'sharing', 'numost']
    
    # Economics data -- like time data but with a different end
    sheets['Economics and costs'] = ['cpi', 'ppp', 'gdp', 'revenue', 'govtexpend', 'totalhealth', 'domestichealth', 'domestichiv', 'globalfund', 'pepfar', 'otherint', 'private', 'health', 'social']

    # Matrix data -- array sizes are population x population
    sheets['Partnerships'] = ['partreg','partcas','partcom','partinj']
    sheets['Transitions']  = ['transasym','transsym']
    
    # Constants -- array sizes are scalars x uncertainty
    sheets['Constants'] = [['trans',    ['mfi', 'mfr', 'mmi', 'mmr', 'inj', 'mtctbreast', 'mtctnobreast']], \
                           ['cd4trans', ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']], \
                           ['prog',     ['acute', 'gt500', 'gt350', 'gt200', 'gt50']],\
                           ['recov',    ['gt500', 'gt350', 'gt200', 'gt50', 'aids']],\
                           ['fail',     ['first', 'second']],\
                           ['death',    ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids', 'treat', 'tb']],\
                           ['eff',      ['condom', 'circ', 'dx', 'sti', 'dis', 'ost', 'pmtct', 'tx', 'prep']],\
                           ['disutil',  ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids','tx']]]
    

    


    ###########################################################################
    ## Load data sheets
    ###########################################################################
    

    ## Basic setup
    data = dict() # Create sheetsure for holding data
    data['date'] = strftime("%Y-%m-%d %H:%M:%S")
    programs = [] # Create sheetsure for holding program data
    try: workbook = open_workbook(filename) # Open workbook
    except: raise Exception('Failed to load spreadsheet: file "%s" not found or other problem' % filename)
    
    ## Loop over each group of sheets
    for sheetname in sheetnames: # Loop over each type of data, but treat constants differently
        sheetgroup = sheets[sheetname]
        for sheet in sheetgroup: # Loop over each workbook for that data -- just one for constants
            lastdatacol = None
            sheetname = sheet[0] # Name of the workbook
            subparlist = sheet[1] # List of subparameters
            sheetdata = workbook.sheet_by_name(sheetname) # Load this workbook
            parcount = -1 # Initialize the parameter count
            printv('  Loading "%s"...' % sheetname, 2, verbose)
            
            
            ## Calculate columns for which data are entered, and store the year ranges
            if sheetname == 'popsizedata': # Need to gather year ranges for epidemic etc. data
                data['epiyears'] = [] # Initialize epidemiology data years
                for col in range(sheetdata.ncols):
                    thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
                    if thiscell=='' and len(data['epiyears'])>0: #  We've gotten to the end
                        lastdatacol = col # Store this column number
                        break # Quit
                    elif thiscell != '': # Nope, more years, keep going
                        data['epiyears'].append(float(thiscell)) # Add this year
            
            # V2 -- this might have to change
            if sheetname == 'econdata': # Need to gather year ranges for economic data
                data['epiyears'] = [] # Initialize epidemiology data years
                for col in range(sheetdata.ncols):
                    thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
                    if thiscell=='' and len(data['epiyears'])>0: #  We've gotten to the end
                        lastdatacol = col # Store this column number
                        break # Quit
                    elif thiscell != '': # Nope, more years, keep going
                        data['epiyears'].append(float(thiscell)) # Add this year
            
            if lastdatacol:  
                assumptioncol = lastdatacol + 1 # The "OR" space is in between
            
            
            
            
            ##################################################################
            ## Now, actually load the data
            ##################################################################
            
            
            # Loop over each row in the workbook
            for row in range(sheetdata.nrows): 
                paramcategory = sheetdata.cell_value(row,0) # See what's in the first column for this row
                
                if paramcategory != '': # It's not blank: e.g. "HIV prevalence"
                    printv('Loading "%s"...' % paramcategory, 3, verbose)
                    parcount += 1 # Increment the parameter count
                    
                    # It's popdata: pull out each of the pieces
                    if sheetname=='popdata': 
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
                    
                    # It's basic data or a matrix: create an empty list
                    elif sheetname in ['popsizedata', 'hivprevdata', 'timedata', 'matrices']: 
                        thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'popsize'
                        data[thispar] = [] # Initialize to empty list
                    
                    # It's economics data
                    elif sheetname in ['econdata']: 
                        thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'popsize'
                        data[thispar] = dict() # Create a sheetsure since need to store future growth assumptions too
                        data[thispar]['past'] = [] # Initialize past data to empty list
                        data[thispar]['future'] = [] # Initialize future assumptions to empty list
                    
                    # It's a constant or a cost: create a sheetsure
                    elif sheetname=='constants': 
                        thispar = subparlist[parcount][0] # Get the name of this parameter, e.g. 'trans'
                        data[thispar] = dict() # Need yet another sheetsure if it's a constant!
                    
                    else:
                        raise Exception('Group name %s not recognized!' % sheetname)
                
                
                
                
                if paramcategory == '': # The first column is blank: it's time for the data
                    subparam = sheetdata.cell_value(row, 1) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
                    
                    if subparam != '': # The subparameter name isn't blank, load something!
                        printv('Parameter: %s' % subparam, 4, verbose)
                        
                        
                        # It's pops-data, split into pieces
                        if sheetname=='popdata': 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=11) # Data starts in 3rd column, finishes in 11th column
                            data[thispar]['short'].append(thesedata[0])

                            data[thispar]['long'].append(thesedata[1])
                            if thispar=='pops':
                                data['pops']['male'].append(forcebool(thesedata[2]))
                                data['pops']['female'].append(forcebool(thesedata[3]))
                                data['pops']['injects'].append(forcebool(thesedata[4]))
                                data['pops']['sexmen'].append(forcebool(thesedata[5]))
                                data['pops']['sexwomen'].append(forcebool(thesedata[6]))
                                data['pops']['sexworker'].append(forcebool(thesedata[7]))
                                data['pops']['client'].append(forcebool(thesedata[8]))

                        
                        # It's key data, save both the values and uncertainties
                        if sheetname in ['popsizedata', 'hivprevdata']:
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
                                try:
                                    validdata = array(thesedata)[~isnan(thesedata)]
                                except:
                                    import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
                                if len(validdata):
                                    invalid = logical_or(array(validdata)>1, array(validdata)<0)
                                    if any(invalid):
                                        column = nonzero(invalid)[0]
                                        raise Exception('Invalid entry in spreadsheet: HIV prevalence (row=%i, column(s)=%s, value=%i)' % (row, column, thesedata[column[0]]))
                            
                        
                        # It's basic data, append the data and check for programs
                        if sheetname=='timedata': 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=lastdatacol) # Data starts in 3rd column
                            thesedata = list(map(lambda val: nan if val=='' else val, thesedata)) # Replace blanks with nan
                            assumptiondata = sheetdata.cell_value(row, assumptioncol)
                            if assumptiondata != '': # There's an assumption entered
                                thesedata = [assumptiondata] # Replace the (presumably blank) data if a non-blank assumption has been entered
                            data[thispar].append(thesedata) # Store data
                            if thispar in ['stiprevulc', 'stiprevdis', 'tbprev', 'hivtest', 'aidstest', 'prep', 'condomreg', 'condomcas', 'condomcom', 'circum',  'sharing']: # All probabilities
                                validdata = array(thesedata)[~isnan(thesedata)]
                                if len(validdata):
                                    invalid = logical_or(array(validdata)>1, array(validdata)<0)
                                    if any(invalid):
                                        column = nonzero(invalid)[0]
                                        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
                                        raise Exception('Invalid entry in spreadsheet: parameter %s (row=%i, column(s)=%s, value=%f)' % (thispar, row+1, column, thesedata[column[0]]))
                            


                        # It's economics data, append the data
                        if sheetname=='econdata': 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=lastdatacol) # Data starts in 3rd column
                            thesedata = list(map(lambda val: nan if val=='' else val, thesedata)) # Replace blanks with nan
                            futuredata = sheetdata.row_values(row, start_colx=assumptioncol, end_colx=assumptioncol+3) # Start from the assumption column and read 3
                            data[thispar]['past'].append(thesedata) # Store data
                            data[thispar]['future'].append(futuredata) # Store data
                        
                        
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
    return data, programs
