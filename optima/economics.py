
'''
Functions to read in the economic data and transform it into time series
'''

from optima import odict, printv, today, smoothinterp
from numpy import nan, isnan, array, logical_or, nonzero

def loadeconomicsspreadsheet(filename='economics.xlsx', verbose=0):
    """
    Loads the economics spreadsheet (i.e. reads its contents into the data).
    Version: 2016jan17
    """
    
    ###########################################################################
    ## Preliminaries
    ###########################################################################
    
    from xlrd import open_workbook # For opening Excel workbooks
    printv('Loading data from %s...' % filename, 1, verbose)
    
    
    def validatedata(thesedata, sheetname, thispar, row, checkupper=False, checkblank=True):
        ''' Do basic validation on the data: at least one point entered, between 0 and 1 or just above 0 if checkupper=False '''
        
        # Check that only numeric data have been entered
        for column,datum in enumerate(thesedata):
            if not isinstance(datum, (int, float)):
                errormsg = 'Invalid entry in sheet "%s", parameter "%s":\n' % (sheetname, thispar) 
                errormsg += 'row=%i, column=%s, value="%s"\n' % (row+1, column, datum)
                errormsg += 'Be sure all entries are numeric'
                raise Exception(errormsg)
        
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
                raise Exception(errormsg)
                
        # No data entered
        elif checkblank:
            errormsg = 'No growth rate assumption entered for parameter "%s", row=%i' % (thispar, row) 
            raise Exception(errormsg)

        return validdata



    def blank2nan(thesedata):
        ''' Convert a blank entry to a nan '''
        return list(map(lambda val: nan if val=='' else val, thesedata))
        
    ##############################################################################
    ## Define the workbook and parameter names -- should match makespreadsheet.py!
    ##############################################################################
        
    sheets = odict()

    # Data 
    subparlist = ['cpi', 'gdp', 'govrev', 'govexp', 'totexp', 'govhealth', 'healthcosts', 'socialcosts']

    ###########################################################################
    ## Load data sheets
    ###########################################################################

    ## Basic setup
    econdata = odict() # Create sheetsure for holding data
    econdata['meta'] = odict()
    econdata['meta']['date'] = today()
    econdata['meta']['sheets'] = sheets # Store parameter names
    try: 
        workbook = open_workbook(filename) # Open workbook
    except: 
        errormsg = 'Failed to load spreadsheet: file "%s" not found or other problem' % filename
        raise Exception(errormsg)
    
    
    ## Calculate columns for which data are entered, and store the year ranges
    sheetdata = workbook.sheet_by_name('Economics and costs') # Load this workbook
    econdata['years'] = [] # Initialize epidemiology data years
    for col in range(sheetdata.ncols):
        thiscell = sheetdata.cell_value(1,col) # 1 is the 2nd row which is where the year data should be
        if thiscell=='' and len(econdata['years'])>0: #  We've gotten to the end
            lastdatacol = col # Store this column number
            break # Quit
        elif thiscell != '': # Nope, more years, keep going
            econdata['years'].append(float(thiscell)) # Add this year
    growthcol = lastdatacol + 1 # Figure out which column the assumptions are in; the "OR" space is in between
    
    ##################################################################
    ## Now, actually load the data
    ##################################################################    
    
    ## Loop over each group of sheets
    parcount = -1 # Initialize the parameter count
    printv('  Loading economic data...', 2, verbose)
        
    # Loop over each row in the workbook, starting from the top
    for row in range(sheetdata.nrows): 
        paramcategory = sheetdata.cell_value(row,0) # See what's in the first column for this row
        subparam = sheetdata.cell_value(row, 1) # Get the name of a subparameter, e.g. 'FSW', population size for a given population
        
        if paramcategory != '': # It's not blank: e.g. "HIV prevalence"
            printv('Loading "%s"...' % paramcategory, 3, verbose)
            parcount += 1 # Increment the parameter count
            try:
                thispar = subparlist[parcount] # Get the name of this parameter, e.g. 'popsize'
            except:
                errormsg = 'Incorrect number of headings found. \n'
                errormsg += 'Check that there is no extra text in the first two columns'
                raise Exception(errormsg)
            econdata[thispar] = dict()
            econdata[thispar]['past'] = [] # Initialize to empty list
            econdata[thispar]['growth'] = [] # Initialize to empty list
                        
        elif subparam != '': # The first column is blank: it's time for the data
            printv('Parameter: %s' % subparam, 4, verbose)
                                
            thesedata = blank2nan(sheetdata.row_values(row, start_colx=2, end_colx=lastdatacol)) # Data starts in 3rd column, and ends lastdatacol-1
            validdata = validatedata(thesedata, 'Economics and costs', thispar, row, checkblank=False)
            econdata[thispar]['past'].append(thesedata) # Store data
            if len(validdata):
                growthdata = blank2nan(sheetdata.row_values(row, start_colx=growthcol, end_colx=growthcol+3))
                validatedata(growthdata, 'Economics and costs', thispar, row, checkblank=True)
                econdata[thispar]['growth'].append(growthdata) 


    printv('...done loading economic data.', 2, verbose)
    return econdata

def makeecontimeseries(econdata, tvec):
    ''' Transform economic data into time series.'''
    econtimeseries = odict()
    
    econtimeseries['tvec'] = tvec

    for thisdatakey in econdata.keys():
        if thisdatakey not in ['meta','years']:
            econtimeseries[thisdatakey] = []
            for row, thesedata in enumerate(econdata[thisdatakey]['past']):
                if len(array(thesedata)[~isnan(thesedata)]):
                    econtimeseries[thisdatakey].append(smoothinterp(newx=tvec, origx=array(econdata['years'])[~isnan(thesedata)], origy=array(thesedata)[~isnan(thesedata)], growth=econdata[thisdatakey]['growth'][row][0]))
                
    return econtimeseries
    
def loadeconomics(filename, tvec, verbose=0):
    ''' Loads spreadsheet and converts to time series'''
    econdata = loadeconomicsspreadsheet(filename,verbose=verbose)
    econtimeseries = makeecontimeseries(econdata, tvec)
    return econdata, econtimeseries
   
def getartcosts(progset, tvec, shortnameofART='ART', growthrateofARTcost=0.02):
    '''Returns an interpolated/extrapolated time series of ART unit costs'''

    newx = tvec
    origx = array(progset.programs[shortnameofART].costcovfn.ccopars['t'])
    origy = array(progset.programs[shortnameofART].costcovfn.getccopar(progset.programs[shortnameofART].costcovfn.ccopars['t'])['unitcost'])
    
    artunitcosts = smoothinterp(newx=newx, origx=origx, origy=origy, growth=growthrateofARTcost)

    return artunitcosts
    
