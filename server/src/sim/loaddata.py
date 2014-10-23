"""
LOADDATA

This function loads the spreadsheet data into Optima.

Version: 2014oct16
"""

#def loaddata(filename='./epi-template.xlsx',verbose=True):
if 1:
    filename='./epi-template.xlsx'
    verbose=True
    
    ###########################################################################
    ## Preliminaries
    ###########################################################################
    
    print('Loading data from %s...' % filename)
    from pylab import nan # For reading in empty values
    from xlrd import open_workbook # For opening Excel spreadsheets
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    
    
    ###########################################################################
    ## Define the spreadsheet and parameter names
    ###########################################################################
    
    sheetnames = [['Epidemiology', 'Testing and treatment', 'Sexual behavior', 'Drug behavior'], ['Partnerships', 'Transitions'], ['Constants']]
    
    basicdata = [['epi',  ['popsize','hivprev','hivprevlow','hivprevhigh','stiprev','tbprev']], \
                 ['txrx', ['testrate','aidstestrate','numtests','numdiagnoses','numinfections','numdeaths','num1stline','num2ndline','numpmtct','numbreastpmtct']], \
                 ['sex',  ['numactsreg','numactscas','numactscom','condomreg','condomcas','condomcom','circum']], \
                 ['drug', ['numinject','sharing','ost']]]
                 
    matrices = [['pships',  ['reg','cas','com','drug']], \
                ['transit', ['asym','sym']]]
    
    constants = [['const', [['trans',    ['mfi','mfr','mmi','mmr','inj','mtct']], \
                            ['cd4trans', ['acute','gt500','gt350','gt200','aids']], \
                            ['prog',     ['acute','gt500','gt350','gt200']],\
                            ['recov',    ['gt500','gt350','gt200','aids']],\
                            ['fail',     ['1st','2nd']],\
                            ['death',    ['background','inj','acute','gt500','gt350','gt200','aids','treat','tb']],\
                            ['eff',      ['condom','circ','dx','sti','meth','pmtct','tx']]]]]
    
    
    ###########################################################################
    ## Load data sheets
    ###########################################################################
    
    data = struct() # Create structure for holding data
    programs = struct() # Create structure for holding program data
    programnames = [] # Create list for storing program names (probably unnecessary?)

    print('opening workbook %s' % filename)
    spreadsheet = open_workbook(filename) # Open spreadsheet
    print('opened workbook %s' % filename)
    print(spreadsheet)

    for i,datanames in enumerate([basicdata, matrices, constants]): # Loop over each type of data, but treat constants differently
        for j in range(len(datanames)): # Loop over each spreadsheet for that data -- just one for constants
            if verbose: print('  Loading "%s"...' % sheetnames[i][j])
            name = datanames[j][0] # Pull out the name of this field, e.g. 'epi'
            namelist = datanames[j][1] # Pull out the list subfields, e.g. ['popsize','hivprev'...]
            data[name] = struct() # Create structure for holding data, e.g. data.epi
            sheetdata = spreadsheet.sheet_by_name(sheetnames[i][j]) # Load this spreadsheet
            parcount = -1 # Initialize the parameter count
            procount = -1 # Initialize the program count
            for r in range(sheetdata.nrows): # Loop over each row in the spreadsheet
                paramcategory = sheetdata.cell_value(r,0) # See what's in the first column for this row
                if len(paramcategory): # It's not blank: e.g. "HIV prevalence"
                    if verbose: print('    Loading "%s"...' % paramcategory)
                    parcount += 1 # Increment the parameter count
                    if i==0 or i==1: # It's basic data or a matrix
                        thispar = namelist[parcount] # Get the name of this parameter, e.g. 'popsize'                    
                        data[name][thispar] = [] # Initialize to empty list
                    if i==2: # It's a constant
                        thispar = namelist[parcount][0] # Get the name of this parameter, e.g. 'trans'
                        data[name][thispar] = struct() # Need yet another structure if it's a constant!

                else: # The first column is blank: it's time for the data
                    subparam = sheetdata.cell_value(r,1) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
                    if len(subparam): # The subparameter name isn't blank, load something!
                        thesedata = sheetdata.row_values(r,start_colx=2,end_colx=20) # Data starts in 3rd column, finishes in 21st column
                        thesedata = map(lambda val: nan if val=='' else val, thesedata) # Replace blanks with nan
                        if i==0: # It's basic data, append the data and check for programs
                            data[name][thispar].append(thesedata) # Store data
                            
                            print('dude this code sucks ccocs')
                            procategory = sheetdata.cell_value(r,19) # See what's in the 18th column - any program data? # WARNING KLUDGY AND AWFUL AND DISGUSTING
                            if len(procategory): # It's not blank: there is a program that affects this parameter
                                if verbose: print('    Loading "%s"...' % procategory)
                                programs[thispar] = struct() # Create structure for storing program details (this is hideous, fix later. Could prob be a list)
                                programs[thispar][subparam] = struct() # Create structure for storing program details (this is hideous, fix later. Could prob be a list)
                                programs[thispar][subparam][procategory] = 1 # Store program name (this is hideous, fix later. Could prob be a list)
                                if sheetdata.cell_value(r,23): # Any behavoiural assumptions to store?
                                    assumptions = sheetdata.row_values(r,start_colx=23,end_colx=24) # Data starts in 3rd column, finishes in 21st column
                                    assumptions = map(lambda val: nan if val=='' else val, assumptions) # Replace blanks with nan
                                    programs[procategory][thispar][subparam].append(assumptions) # Store data in form program name/beahviour/pop
                            
                        if i==1: # It's a matrix, append the data 
                            data[name][thispar].append(thesedata) # Store data
                                                        
                        if i==2: # It's a constant, create a new dictionary entry
                            subpar = namelist[parcount][1].pop(0) # Pop first entry of subparameter list, which is namelist[parcount][1]
                            data[name][thispar][subpar] = thesedata # Store data
    
    if verbose: print('  ...done loading data.')
#    return data