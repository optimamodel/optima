"""
LOADSPREADSHEET

This function loads the spreadsheet data into Optima.

Version: 2014oct29
"""

def loadspreadsheet(filename='example.xlsx',verbose=2):

    ###########################################################################
    ## Preliminaries
    ###########################################################################
    
    if verbose>=1: print('Loading data from %s...' % filename)
    from matplotlib.pylab import nan, array # For reading in empty values
    from xlrd import open_workbook, XL_CELL_BLANK, XL_CELL_EMPTY # For opening Excel spreadsheets
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    
    
    ###########################################################################
    ## Define the spreadsheet and parameter names
    ###########################################################################
    
    sheetnames = [['Programs'], \
                  ['Epidemiology', 'Testing and treatment', 'Sexual behavior', 'Drug behavior'], \
                  ['Partnerships', 'Transitions'], \
                  ['Constants', 'Economics'], \
                  ['Cost and coverage']]
    
    meta = [['meta', ['pops', 'progs']]]
    
    basicdata = [['epi',  ['popsize','hivprev','hivprevlow','hivprevhigh','stiprev','tbprev']], \
                 ['txrx', ['testrate','aidstestrate','numtests','numdiagnoses','numinfections','numdeaths','numfirstline','numsecondline','numpmtct','numbreastpmtct']], \
                 ['sex',  ['numactsreg','numactscas','numactscom','condomreg','condomcas','condomcom','circum']], \
                 ['drug', ['numinject','sharing','ost']]]
                 
    matrices = [['pships',  ['reg','cas','com','drug']], \
                ['transit', ['asym','sym']]]
    
    constants = [['const', [['trans',    ['mfi','mfr','mmi','mmr','inj','mtct']], \
                            ['cd4trans', ['acute','gt500','gt350','gt200','aids']], \
                            ['prog',     ['acute','gt500','gt350','gt200']],\
                            ['recov',    ['gt500','gt350','gt200','aids']],\
                            ['fail',     ['first','second']],\
                            ['death',    ['background','inj','acute','gt500','gt350','gt200','aids','treat','tb']],\
                            ['eff',      ['condom','circ','dx','sti','meth','pmtct','tx']]]], \
                ['econ',   [['dalys',    ['acute','gt500','gt350','gt200','aids','tx']], \
                            ['costs',    ['acute','gt500','gt350','gt200','aids']]]]]
    
    costcov = [['costcov',  ['cost', 'cov']]]
    
    dud_types = set([XL_CELL_BLANK, XL_CELL_EMPTY])

    def is_empty_row(worksheet, row_number):
        rowf = set([ ty for ty in worksheet.row_types(row_number) ])
        return (rowf.union(dud_types)==dud_types)

    ###########################################################################
    ## Load data sheets
    ###########################################################################
    
    data = struct() # Create structure for holding data
    data.__doc__ = 'Raw data as loaded from the spreadsheet, including both epidemiological and behavioral data, plus economics and velociraptors.'
    programs = struct() # Create structure for holding program data
    programs.__doc__ = 'Parameters that define the HIV programs -- cost-coverage and coverage-outcome curves.'
    spreadsheet = open_workbook(filename) # Open spreadsheet

    for sheettype,datanames in enumerate([meta, basicdata, matrices, constants, costcov]): # Loop over each type of data, but treat constants differently
        for dataname in range(len(datanames)): # Loop over each spreadsheet for that data -- just one for constants
            
            if verbose>=2: print('  Loading "%s"...' % sheetnames[sheettype][dataname])
            name = datanames[dataname][0] # Pull out the name of this field, e.g. 'epi'
            namelist = datanames[dataname][1] # Pull out the list subfields, e.g. ['popsize','hivprev'...]
            data[name] = struct() # Create structure for holding data, e.g. data.epi
            sheetdata = spreadsheet.sheet_by_name(sheetnames[sheettype][dataname]) # Load this spreadsheet
            parcount = -1 # Initialize the parameter count
            
            if sheettype==1: # Initialize row counts
                lastcol = sheetdata.ncols - 8 # The 8 makes sense...
                assumptioncol = lastcol + 1 # The "OR" space is in between
                programcols = assumptioncol + array([3,5,7]) # Sorry for the weird numbering...not sure what the deal is
            
            
            # Loop over each row in the spreadsheet
            for row in range(sheetdata.nrows): 
                empty_previous_row = row>0 and is_empty_row(sheetdata, row-1)

                paramcategory = sheetdata.cell_value(row,0) # See what's in the first column for this row
                has_title = False
                has_data = False

                if (paramcategory!='' and (row==0 or empty_previous_row)): has_title = True

                if (sheettype!=2 and paramcategory==''): has_data = True
                if (sheettype==2 and paramcategory!='' and (row>1 and not empty_previous_row)): has_data = True

                print ("row: %s empty: %s, has_data: %s has_title: %s" % (row, empty_previous_row, has_data, has_title))


                if has_title: # It's not blank: e.g. "HIV prevalence"
                    if verbose>=2: print('    Loading "%s"...' % paramcategory)
                    parcount += 1 # Increment the parameter count

                    print("sheettype=%s namelist = %s parcount = %s" % (sheettype, namelist, parcount))
                    
                    if sheettype==0: # Metadata
                        thispar = namelist[parcount] # Get the name of this parameter, e.g. 'pop'
                        data[name][thispar] = struct() # Initialize to empty list
                        data[name][thispar].short = []
                        data[name][thispar].long = []
                        if parcount==0:
                            data[name][thispar].male = []
                            data[name][thispar].pwid = []
                    
                    if sheettype==1 or sheettype==2 or sheettype==4: # It's basic data or a matrix
                        thispar = namelist[parcount] # Get the name of this parameter, e.g. 'popsize'                    
                        data[name][thispar] = [] # Initialize to empty list
                    
                    if sheettype==3: # It's a constant
                        thispar = namelist[parcount][0] # Get the name of this parameter, e.g. 'trans'
                        data[name][thispar] = struct() # Need yet another structure if it's a constant!

                
                if has_data: # The first column is blank: it's time for the data
                    subpar_index = 0 if sheettype == 2 else 1 # matrix does not have an empty column to the left
                    subparam = sheetdata.cell_value(row, subpar_index) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
                    print ("paramcategory = %s, subparam = %s, subpar_index = %s" % (paramcategory, subparam, subpar_index))
                    if not(subparam==''): # The subparameter name isn't blank, load something!
                        
                        # It's meta-data, split into pieces
                        if sheettype==0: 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=6) # Data starts in 3rd column, finishes in 6th column
                            data[name][thispar].short.append(thesedata[0])
                            data[name][thispar].long.append(thesedata[1])
                            if parcount==0:
                                data[name][thispar].male.append(thesedata[2])
                                data[name][thispar].pwid.append(thesedata[3])
                        
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
                        if sheettype==2: 
                            thesedata = sheetdata.row_values(row, start_colx=1, end_colx=15) # Data starts in 2nd column, finishes in 14th column
                            thesedata = map(lambda val: 0 if val=='' else val, thesedata) # Replace blanks with nan
                            data[name][thispar].append(thesedata) # Store data
                        
                        # It's a constant, create a new dictionary entry
                        if sheettype==3: 
                            thesedata = sheetdata.row_values(row, start_colx=2, end_colx=5) # Data starts in 3rd column, finishes in 5th column
                            thesedata = map(lambda val: 0 if val=='' else val, thesedata) # Replace blanks with nan
                            subpar = namelist[parcount][1].pop(0) # Pop first entry of subparameter list, which is namelist[parcount][1]
                            data[name][thispar][subpar] = thesedata # Store data
    
    if verbose>=2: print('  ...done loading data.')
    return data, programs
