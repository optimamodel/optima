import optima as op
from numpy import nan, isnan, mean, concatenate as cat, array, exp, append, all

__all__ = [
    'migrate',
    'loadproj',
    'loadportfolio',
    'optimaversion',
    'migraterevisionfunc',
]

_pardefinitions = None # Store the pardefinitions so we don't have to load multiple times

##########################################################################################
### MIGRATION DEFINITIONS
##########################################################################################

def setmigrations(which='migrations'):
    '''
    Define the migrations -- format is 
        'current_version': ('new_version', function, 'date', 'string description of change')
    
    If "which" is anything other than "changelog", then return the list of migrations.
    Otherwise, return the changelog (just the new version and message).
    
    Version: 2017may23
    '''

    migrations = op.odict([
        # Orig     New       Date         Migration           Description
        ('2.0',   ('2.0.0', '2016-07-19', None,              'Converted version number to string')),
        ('2.0.0', ('2.0.1', '2016-07-20', addscenuid,        'Added UID to scenarios')),
        ('2.0.1', ('2.0.2', '2016-07-29', addforcepopsize,   'Added option for forcing population size to match')),
        ('2.0.2', ('2.0.3', '2016-08-25', delimmediatecare,  'Removed immediate care parameter')),
        ('2.0.3', ('2.0.4', '2016-08-31', addproppmtct,      'Added new parameter -- proportion on PMTCT')),
        ('2.0.4', ('2.1',   '2016-09-12', redotransitions,   'Major update to how transitions in health states are handled')),
        ('2.1',   ('2.1.1', '2016-10-02', makepropsopt,      'Removed data on proportion parameters')),
        ('2.1.1', ('2.1.2', '2016-10-05', addalleverincare,  'Included new setting to store everyone in care')),
        ('2.1.2', ('2.1.3', '2016-10-18', removenumcircdata, "Don't store data on number circumcised")),
        ('2.1.3', ('2.1.4', '2016-10-18', removepopchardata, "Don't store sex worker and injecting characteristics")),
        ('2.1.4', ('2.1.5', '2016-11-01', addaidsleavecare,  'Added new parameter -- AIDS leave care percentage')),
        ('2.1.5', ('2.1.6', '2016-11-01', addaidslinktocare, 'Added new parameter -- AIDS link to care duration')),
        ('2.1.6', ('2.1.7', '2016-11-03', adddataend,        'Separated dataend from end')),
        ('2.1.7', ('2.1.8', '2016-11-07', fixsettings,       'Added new attributes to settings')),
        ('2.1.8', ('2.1.9', '2016-12-22', addoptimscaling,   'Added a budget scaling parameter to optimizations')),
        ('2.1.9', ('2.1.10','2016-12-28', addpropsandcosttx, 'Added treatment cost parameter')),
        ('2.1.10',('2.2',   '2017-01-13', redoparameters,    'Updated the way parameters are handled')),
        ('2.2',   ('2.2.1', '2017-02-01', redovlmon,         'Updated the VL monitoring parameter')),
        ('2.2.1', ('2.2.2', '2017-02-01', addprojectinfo,    'Stored information about the project in the results')),
        ('2.2.2', ('2.3',   '2017-02-09', redoparamattr,     'Updated parameter attributes')),
        ('2.3',   ('2.3.1', '2017-02-15', removespreadsheet, "Don't store the spreadsheet with the project, to save space")),
        ('2.3.1', ('2.3.2', '2017-03-01', addagetopars,      'Ensured that age is stored in parsets')),
        ('2.3.2', ('2.3.3', '2017-03-02', redotranstable,    'Split transition table into two tables to speed processing')),
        ('2.3.3', ('2.3.4', '2017-03-30', redotranstable,    'Added aditional fixes to the transition table')),
        ('2.3.4', ('2.3.5', '2017-04-18', None,              'Added migrations for portfolios')),
        ('2.3.5', ('2.3.6', '2017-04-21', None,              'Fixed PMTCT calculations')),
        ('2.3.6', ('2.3.7', '2017-05-13', None,              'Changed plotting syntax')),
        ('2.3.7', ('2.3.8', '2017-05-23', None,              'Malawi: Many minor changes to plotting, parameters, etc.')),
        ('2.3.8', ('2.4',   '2017-06-05', None,              'Ukraine: ICER analysis; cascade bar plot; GUI tools; summary() and fixprops() methdods')),
        ('2.4',   ('2.5',   '2017-07-03', None,              'Made registration public')),
        ('2.5',   ('2.6',   '2017-10-23', None,              'Public code release')),
        ('2.6',   ('2.6.1', '2017-12-19', None,              'Scenario sensitivity feature')),
        ('2.6.1', ('2.6.2', '2017-12-19', None,              'New results format')),
        ('2.6.2', ('2.6.3', '2018-01-17', addtimevarying,    'Preliminaries for time-varying optimization')),
        ('2.6.3', ('2.6.4', '2018-01-24', None,              'Changes to how proportions are handled')),
        ('2.6.4', ('2.6.5', '2018-04-03', None,              'Changes to how HIV+ births are handled')),
        ('2.6.5', ('2.6.6', '2018-04-25', addtreatbycd4,     'Updates CD4 handling and interactions between programs')),
        ('2.6.6', ('2.6.7', '2018-04-26', None,              'Handle male- and female-only populations for parameters')),
        ('2.6.7', ('2.6.8', '2018-04-28', removecosttx,      'Remove treatment cost parameter')),
        ('2.6.8', ('2.6.9', '2018-04-28', addrelhivdeath,    'Add population-dependent relative HIV death rates')),
        ('2.6.9', ('2.6.10','2018-05-16', addspectrumranges, 'Add ranges for optional data inputs')),
        ('2.6.10',('2.6.11','2018-05-21', circmigration,     'Adds the missing migration for circumcision key changes')),
        ('2.6.11',('2.6.12','2018-05-23', changehivdeathname,'Change the name of the relative HIV-related death rate')),
        ('2.6.12',('2.7',   '2018-05-25', tvtreatfail,       'Redo treatment failure and add regimen switching/adherence support')),
        ('2.7',   ('2.7.1', '2018-06-17', None,              'Modified minimize money algorithm')),
        ('2.7.1', ('2.7.2', '2018-07-24', addfixedattr,      'Store whether or not proportions are fixed')),
        ('2.7.2', ('2.7.3', '2018-07-26', addpopfactor,      'Add a population adjustment factor to programs')),
        ('2.7.3', ('2.7.4', '2018-07-27', addpopfactor,      'Fix previous migration')),
        ('2.7.4', ('2.7.5', '2018-10-02', None,              'Update minimize money algorithm')),
        ('2.7.5', ('2.7.6', '2018-12-11', None,              'Disable initpeople for optimization')),
        ('2.7.6', ('2.8.0', '2019-01-09', None,              'Python 3 compatibility')),
        ('2.8.0', ('2.8.1', '2019-07-10', None,              'Additional changes for Python 3')),
        ('2.8.1', ('2.8.2', '2019-08-07', None,              'Update to money minimization algorithm')),
        ('2.8.2', ('2.9.0', '2019-10-11', addcascadeopt,     'Add cascade optimization objectives')),
        ('2.9.0', ('2.9.1', '2019-12-02', fixcascadeopt,     'Fix cascade optimization objectives')),
        ('2.9.1', ('2.9.2', '2019-12-04', None,              'Add PrEP for injection-related infections')),
        ('2.9.2', ('2.9.3', '2020-02-24', None,              'Improves scenario export, changes district budget allocation algorithm, and contains frontend fixes')),
        ('2.9.3', ('2.9.4', '2020-02-25', addprogdefault,    'Add default values for parameters in absence of programs')),
        ('2.9.4', ('2.10.0','2021-02-09', addpepreturntocare,'Add PEP parameters, rename PrEP parameters, and add a return to care parameter distinct from link to care')),
        ('2.10.0',('2.10.1','2021-02-09', updatedisutilities,'Update disutility weights for HIV to match GBD 2019')),
        ('2.10.1',('2.10.2','2022-01-28', updateprepconstants,'Update constants for PrEP, PEP, and ART efficacy for all parsets')),
        ('2.10.2',('2.10.3','2022-07-11', addageingrates,    'Update ageing to allow non-uniform age rates')),
        ('2.10.3',('2.10.4','2022-07-12', partlinearccopars, 'Update cost-coverage curves to be linear to saturation_low then non-linear to saturation high')),
        ('2.10.4',('2.10.5','2022-07-13', None ,             'Rename optional indicators in the databook to align with UNAIDS terminology')),
        ('2.10.5',('2.10.6','2022-07-14', removerequiredvl,  'Remove the required VL parameter to better capture treatment failure identification')),
        ('2.10.6',('2.10.7','2022-07-17', addmetapars,       'Add/change meta parameters for forcepopsize, allcd4eligibletx, initcd4weight, rrcomorbiditydeathtx, relhivbirth')),
        ('2.10.7',('2.10.8','2022-07-20', adjustreturnpar,   'Change return to care to be a rate instead of a duration')),
        ('2.10.8',('2.10.9','2022-07-20', None,              'Make popfactor apply directly to target population size, instead of the function for coverage')),
        ('2.10.9',('2.10.10','2022-08-09',None,              'Compatibility and FE updates')),
        ('2.10.10',('2.10.11','2022-08-09',fixmanfitsettings,'Fix manual fit settings (which impact on FE display)')),
        ('2.10.11',('2.10.12','2022-08-31',popgrowthoptions, 'Change forcepopsize to be forcepopgrowth by population and impact differently on key pops without inflows')),
        ('2.10.12',('2.10.13','2022-09-01',migrationmigration,'Add migration parameters and modeling')),
        ('2.10.13',('2.10.14','2022-09-06',addsexinjmtctsettings,'Add sex, inj, and mtct indices to settings')),
        ('2.10.14',('2.10.15','2022-09-13',fixmoremanfitsettings,'Fix more manual fit settings (which impact on FE display)')),
        ('2.10.15',('2.10.16','2022-09-15',clearuntrackedresults,'Clear results if they did not have tracking')),
        ('2.10.16',('2.11.0', '2022-09-17', None,            'Version update for updated GUI launch')),
        ('2.11.0', ('2.11.1', '2022-10-06', None,            'Major bug fixes, FE updates, fixproppmtct now fixes proportion of diagnosed women on PMTCT and propcare brings people from dx and lost')),
        ('2.11.1', ('2.11.2', '2022-10-10', None,            'Big model speed ups (about 25%) and split diagnoses by CD4 count')),
        ('2.11.2', ('2.11.3', '2022-11-02', None,            'Annual data takes precedence over assumption when loading databook, bug fixes, FE Scenario tab add stacked for one scenario + other things.')),
        ('2.11.3', ('2.11.4', '2023-02-07',addallconstraintsoptim, 'Adds absconstraints and proporigconstraints to Optim, model works with initpeople and optimization improvements')),
        ('2.11.4', ('2.12.0', '2023-03-10',addinsertonlyacts,'Adds ANC testing to diagnose mothers to put onto PMTCT, actsreg etc only contain insertive acts, and relhivbirth only reduces birth rate of diagnosed HIV+ potential mothers.')),
        ('2.12.0', ('2.12.1', '2024-05-27',fixzeronumcircparset,'Reloads numcirc "Number of voluntary medical male circumcisions" from data - was previously overriden to be zero')),
        ('2.12.1', ('2.12.2', '2024-07-12',None ,            'Fix MTCT: previously double-counting MTCT of people on ART')),
        ])
    
    
    # Define changelog
    changelog = op.odict()
    for ver,date,migrator,msg in migrations.values():
        changelog[ver] = date+' | '+msg
    
    # Return the migrations structure, unless the changelog is specifically requested
    if which=='changelog': return changelog
    else:                  return migrations


def setrevisionmigrations(which='migrations'):
    '''
    Define the migrations -- format is
        'current_version': ('new_version', function, 'date', 'string description of change')

    If "which" is anything other than "changelog", then return the list of migrations.
    Otherwise, return the changelog (just the new version and message).

    Version: 2017may23
    '''

    migrations = op.odict([
        # Orig     New       Date         Migration           Description
        ('0',   ('1',  '2023-10-17', parsandprograms_odictcustom,    'Add P.revision, change Parameterset.pars and Programset.programs from odict to odict_custom and link them')),
        ('1',   ('2',  '2023-12-04', None,                           'Fix bug when deep-copying a `Parameterset`, the `pars` from a different `Parameterset` would get copied in certain cases')),
        ('2',   ('3',  '2024-01-18', None,                           'Fix small unpickling bug and FE raises BadFileFormatError when uploading project that it cannot unpickle')),
        ('3',   ('4',  '2024-01-18', updatemethodsettings,           'Update methods so `numinciallmethods` is split by regular, casual, commercial')),
        ('4',   ('5',  '2024-06-26', None,                           'Update sampling of parameters to use default_rng to sample more randomly between parameters')),
        ('5',   ('6',  '2024-07-16', resetnumcircfromdata,           'Reset the fromdata attribute of the numcirc parameter to allow it to be updated')),
        ('6',   ('7',  '2024-08-26', None,                           'Add most "other" outputs to the standard excel sheet with optional argument')),
        ('7',   ('8',  '2024-09-27', None,                           'Update definition of "latediag" to be CD4<350 (and add separate output for undiagCD4<350 to align)')),
        ('8',   ('9',  '2024-10-07', None,                           'Update calculation of ICERs')),
        ('9',   ('10', '2024-10-09', None,                           'Add objective option for minimising number of prevalent undiagnosed HIV infections')),
        ('10',  ('11', '2024-11-01', None,                           'A couple of FE fixes')),
        ('11',  ('12', '2025-09-13', refreshlinks,                   'Add options for sensitivity runs and improvements')),
        ])


    # Define changelog
    changelog = op.odict()
    for ver,date,migrator,msg in migrations.values():
        changelog[ver] = date+' | '+msg

    # Return the migrations structure, unless the changelog is specifically requested
    if which=='changelog': return changelog
    else:                  return migrations



##########################################################################################
### MIGRATION UTILITIES
##########################################################################################

def optimaversion(filename=None, version=None, branch=None, sha=None, verbose=False, die=False):
    '''
    Reads the current script file and adds Optima version info. Simply add the line
    
        optimaversion(__file__)
    
    to a script file, and on running it will automatically re-save it as e.g.
    
        optimaversion(__file__) # Version: 2.1.11 | Branch: optima-version-for-scripts | SHA: e2620b
    
    Note: you can also use e.g. op.optimaversion(__file__), as long as "optimaversion(__file__)" appears. 
    If version, branch, or sha arguments are supplied, then it will raise an exception if they 
    don't match, e.g.
    
        optimaversion(__file__, version='2.1.4')
    
    Version: 2017jan29
    '''
    
    # Preliminaries
    shalength = 6 # Don't use the whole thing, it's ugly and unnecessary
    if filename is None: # Check to make sure a file name is given
        errormsg = 'Please call this function like this: optimaversion(__file__)'
        if die: raise op.OptimaException(errormsg)
        else: print(errormsg); return None
    currversion = op.supported_versions # Get Optima version info
    currbranch,currsha = op.gitinfo(die=die) # Get git info, dying on failure if requested
    if version is not None and version not in currversion: # Optionally check that versions match
        errormsg = 'Actual version does not match requested version (%s vs. %s)' % (currversion, version)
        raise op.OptimaException(errormsg)
    if branch is not None and branch!=currbranch: # Optionally check that versions match
        errormsg = 'Actual branch does not match requested branch (%s vs. %s)' % (currbranch, branch)
        raise op.OptimaException(errormsg)
    if sha is not None:
        validshalength = min(len(sha), shalength)
        if sha[:validshalength+1]!=currsha[:validshalength+1]: # Optionally check that versions match
            errormsg = 'Actual SHA does not match requested SHA (%s vs. %s)' % (currsha[:validshalength+1], sha[:validshalength+1])
            raise op.OptimaException(errormsg)
    versionstring = ' # Version: %s (%s) | Branch: %s | SHA: %s\n' % (currversion, op.revision, currbranch, currsha[:shalength+1]) # Create string to write
    strtofind = 'optimaversion(' # String to look for -- note, must exactly match function call!

    # Read script file
    try: 
        f = open(filename, 'r')
    except:
        errormsg = 'Could not open file "%s" for reading' % filename
        if die: raise op.OptimaException(errormsg)
        else: print(errormsg); return None
    if verbose: print('Reading file %s' % filename)
    alllines = f.readlines() # Read all lines in the file
    origlines = op.dcp(alllines) # Keep a copy of the original version of the file
    notfound = True # By default, fail
    for l,line in enumerate(alllines): # Loop over each line
        ind = line.find(strtofind) # Look for string to find
        if ind>=0: # If found...
            if verbose: print('Found function call at line %i' % l)
            if line.count(')')!=1: # If it's not a usual function call, give up
                errormsg = 'optimaversion got confused by this line with more or less than one ")": "%s"' % line
                if die: raise op.OptimaException(errormsg)
                else: print(errormsg); return None
            functionend = line.find(')')+1 # Find the end of the function (inclusive)
            alllines[l] = line[:functionend]+versionstring # Replace with version info
            notfound = False # It's not a failure
            break # Don't keep looking
    if notfound: # Couldn't find it
        errormsg = 'Could not find call to optimaversion() in %s' % filename
        if die: raise op.OptimaException(errormsg)
        else: print(errormsg); return None
    f.close()
        
    # Write script file, but only if something changed
    if alllines!=origlines:
        try: 
            f = open(filename, 'w')
        except:
            errormsg = 'Could not open file "%s" for writing' % filename
            if die: raise op.OptimaException(errormsg)
            else: print(errormsg); return None
        if verbose: print('Writing file %s' % filename)
        try: 
            f.writelines(alllines) # Just write everything, but only if something's changed
        except: 
            errormsg = 'optimaversion() write failed on %s' % filename
            if die: raise op.OptimaException(errormsg)
            else: print(errormsg); return None
        f.close()
    
    return None


def addparameter(project=None, copyfrom=None, short=None, type='time', **kwargs):
    '''
    DO SUPPLY THE CORRECT TYPE - SEE KNOWNTYPES in addblankdata() - it should match the model-inputs.xlsx | Data inputs | type column
    Function for adding a new parameter to a project -- used by several migrations.
    Use kwargs to arbitrarily specify the new parameter's properties.
    type is used to create the blank data, and should correspond to the type column in model-inputs.xlsx:Data inputs
    '''
    for ps in project.parsets.values():
        if op.compareversions(project.version, '2.2')>=0: # Newer project, pars is dict
            ps.pars[short] = op.dcp(project.pars()[copyfrom])
            ps.pars[short].short = short
            for kwargkey,kwargval in kwargs.items():
                setattr(ps.pars[short], kwargkey, kwargval)
        else: # Older project, pars is list of dicts
            for i in range(len(ps.pars)):
                ps.pars[i][short] = op.dcp(project.pars()[0][copyfrom])
                ps.pars[i][short].short = short
                for kwargkey,kwargval in kwargs.items():
                    setattr(ps.pars[i][short], kwargkey, kwargval)

    if copyfrom in project.data:
        # addblankdata1(project=project, short=short, **kwargs)
        addblankdata(project=project, short=short, copyfrom=copyfrom, type=type, **kwargs)

    return None


def addblankdata(project=None, short=None, copyfrom=None, type='time', verbose=2, die=False, **kwargs):
    '''
    DO SUPPLY THE CORRECT TYPE - SEE KNOWNTYPES - it should match the model-inputs.xlsx | Data inputs | type column
    Note that this assumes certain type of shapes, and simply fills in constants with nan
    '''

    errmsg = None
    knowntypes = ['key', 'time', 'matrix', 'constant']
    if type not in knowntypes:
        errmsg = f"Cannot create blank data using type={type} in addblankdata2, need to pass a known type: {knowntypes}"
    if copyfrom is None or copyfrom in ['meta', 'pops', 'pships', 'years', 'npops']:
        errmsg = f'Cannot copy data using copyfrom={copyfrom} in addblankdata2, need to pass a (better) parameter to copyfrom'
    if errmsg:
        if die: raise op.OptimaException(errmsg)
        else: print('WARNING: '+errmsg)
        return

    copyfromdata = project.data[copyfrom]

    if type == 'constant': # This is a constant with shape (3,)
        project.data[short] = [nan, nan, nan]

    elif type == 'time': # This is a parameter with shape (x, npts)
        x    = len(copyfromdata)
        npts = len(project.data['years'])  # P.data[copyfrom] could be (x, 1) if it is only assumptions

        project.data[short] = [[nan] * npts] * x

    elif type == 'matrix': # matrix with shape (x,y)
        x = len(copyfromdata)
        y = len(copyfromdata[0])
        project.data[short] = [[0] * y] * x

    elif type == 'key': # This is a 'key' parameter (popsize, hivprev) with shape (3, x, npts)
        x    = len(copyfromdata[0])
        npts = len(project.data['years'])  # P.data[copyfrom] could be (3, x, 1) if it is only assumptions

        project.data[short] = [ [[nan]*npts] * x ] * 3

    else:
        raise op.OptimaException(f'Cannot copy data from parameter "{copyfrom}" as it has an unknown type: {type}')

    return

### This version is different in that it loads in what the new parameter is supposed to be (which takes a little bit of time) and uses that,
### rather than type being an input
# def addblankdata2(project=None, short=None, verbose=2, die=False, **kwargs):
#     if project.data is None or 'pops' not in project.data:
#         errmsg = f'Cannot add blank data for input: "{short}" since project.data is missing population definitions'
#         if die: raise op.OptimaException(errmsg)
#         else: print(errmsg)
#         return
#
#     global _pardefinitions  # The reason we can save this globally is that op.loaddatapars will always return the same thing
#     if _pardefinitions is None:
#         _pardefinitions = op.loaddatapars(verbose=verbose)
#
#     datainputs    = {d['short']:d for d in _pardefinitions['Data inputs']}
#     dataconstants = {d['short']:d for d in _pardefinitions['Data constants']}
#
#     if short in datainputs.keys():
#         definition = datainputs[short]
#         npops = len(getpopsfromrangename(project.data, definition['rownames'], **kwargs))
#         npts  = len(project.data['years'])
#
#         if definition['type'] == 'key':
#             project.data[short] = [ [[nan]*npts] * npops ] * 3  # (3, npops, npts) = empty data
#         elif definition['type'] == 'matrix':
#             project.data[short] = [ [0] * npops ] * npops  # (npops, npops) = empty matrix
#         else: # definition['type'] == 'time':
#             project.data[short] = [[nan]*npts] * npops    # (npops, npts) = empty data
#
#     elif short in dataconstants.keys():
#         definition = dataconstants[short]
#         project.data[short] = [definition['best'], definition['low'], definition['high']]
#
#     else: # Not in current data inputs or constants, assume it is removed in this version - or it's something like meta, pops, pships, years, npops
#         return
#
# def getpopsfromrangename(data, rangename, **kwargs):
#     # Based off OptimaSpreadsheet.getrange()
#     if    rangename=='allpops':  return data['pops']['short']
#     elif  rangename=='females':  return [data['pops']['short'][i] for i, female in enumerate(data['pops']['female']) if female]
#     elif  rangename=='males':    return [data['pops']['short'][i] for i, male in enumerate(data['pops']['male']) if male]
#     elif  rangename=='children': return [data['pops']['short'][i] for i, age in enumerate(data['pops']['age']) if age[0]==0]
#     elif  rangename=='average':  return ['Average']
#     elif  rangename=='total':    return ['Total']
#     elif  rangename=='hbl':      return ['high','best','low']
#     elif  rangename=='.':        return None
#     else:
#         errormsg = 'Range name %s not found' % rangename
#         raise Exception(errormsg)
#     return None

def removeparameter(project=None, short=None, datashort=None, verbose=False, die=False, **kwargs):
    ''' 
    Remove a parameter from a parset
    '''
    if short is not None:
        for ps in project.parsets.values():
            if op.compareversions(project.version, '2.2')>=0: # Newer project, pars is dict
                try: ps.pars.pop(short) # Fail loudly
                except:
                    if verbose: print('Failed to remove parameter %s' % short)
                    if die: raise
            else: # Older project, pars is list of dicts
                for i in range(len(ps.pars)):
                    try: ps.pars[i].pop(short) # Fail loudly
                    except:
                        if verbose: print('Failed to remove parameter %s' % short)
                        if die: raise
    if datashort is not None:
        try: project.data.pop(datashort) # Fail loudly
        except:
            if verbose: print('Failed to remove data parameter %s' % datashort)
            if die: raise
    return None





##########################################################################################
### PROJECT MIGRATIONS
##########################################################################################
    

def addscenuid(project, **kwargs):
    """
    Migration between Optima 2.0.0 and 2.0.1.
    """
    for scen in project.scens.values():
        if not hasattr(scen, 'uid'):
            scen.uid = op.uuid()
    return None


def addforcepopsize(project, **kwargs):
    """
    Migration between Optima 2.0.1 and 2.0.2.
    """
    if not hasattr(project.settings, 'forcepopsize'):
        project.settings.forcepopsize = True
    return None


def delimmediatecare(project, **kwargs):
    """
    Migration between Optima 2.0.2 and 2.0.3 -- WARNING, will this work for scenarios etc.?
    """
    removeparameter(project, short='immediatecare', datashort='immediatecare')
    return None


def addproppmtct(project, **kwargs):
    """
    Migration between Optima 2.0.3 and 2.0.4.
    """
    addparameter(project=project, copyfrom='proptx', short='proppmtct', name='Pregnant women and mothers on PMTCT')
    return None


def redotransitions(project, dorun=False, **kwargs):
    """
    Migration between Optima 2.0.4 and 2.1
    """
    from numpy import concatenate as cat

    # Update settings
    project.settings.healthstates = ['susreg', 'progcirc', 'undx', 'dx', 'care', 'usvl', 'svl', 'lost']
    project.settings.notonart = cat([project.settings.undx,project.settings.dx,project.settings.care,project.settings.lost])
    project.settings.alldx = cat([project.settings.dx,project.settings.care,project.settings.usvl,project.settings.svl,project.settings.lost])
    project.settings.allcare = cat([project.settings.care,project.settings.usvl,project.settings.svl])

    project.settings.allplhiv  = cat([project.settings.undx, project.settings.alldx])
    project.settings.allstates = cat([project.settings.sus, project.settings.allplhiv]) 
    project.settings.nstates   = len(project.settings.allstates) 
    project.settings.statelabels = project.settings.statelabels[:project.settings.nstates]
    project.settings.nhealth = len(project.settings.healthstates)
    project.settings.transnorm = 0.85 # Warning: should NOT match default since should reflect previous versions, which were hard-coded as 1.2 (this being close to the inverse of that, value determined empirically)

    if hasattr(project.settings, 'usecascade'): del project.settings.usecascade
    if hasattr(project.settings, 'tx'):         del project.settings.tx
    if hasattr(project.settings, 'off'):        del project.settings.off

    # Update variables in data
    oldtimepars = ['immediatecare', 'biofailure', 'restarttreat','stoprate', 'treatvs']
    for oldpar in oldtimepars:
        project.data.pop(oldpar, None)
        for key,progset in project.progsets.items():
            if oldpar in progset.covout.keys():
                msg = 'Project includes a program in program set "%s" that affects "%s", but this parameter has been removed' % (key, oldpar)
                project.addwarning(msg)

    # Add new constants
    project.data['const']['deathsvl']       = [0.23,    0.15,   0.3]
    project.data['const']['deathusvl']      = [0.4878,  0.2835, 0.8417]
    project.data['const']['svlrecovgt350']  = [2.2,     1.07,   7.28]
    project.data['const']['svlrecovgt200']  = [1.42,    0.9,    3.42]
    project.data['const']['svlrecovgt50']   = [2.14,    1.39,   3.58]
    project.data['const']['svlrecovlt50']   = [0.66,    0.51,   0.94]
    project.data['const']['treatfail']      = [0.16,    0.05,   0.26]
    project.data['const']['treatvs']        = [0.2,     0.1,    0.3]
    project.data['const']['usvlproggt500']  = [0.026,   0.005,  0.275]
    project.data['const']['usvlproggt350']  = [0.1,     0.022,  0.87]
    project.data['const']['usvlproggt200']  = [0.162,   0.05,   0.869]
    project.data['const']['usvlproggt50']   = [0.09,    0.019,  0.723]
    project.data['const']['usvlrecovgt350'] = [0.15,    0.038,  0.885]        
    project.data['const']['usvlrecovgt200'] = [0.053,   0.008,  0.827]
    project.data['const']['usvlrecovgt50']  = [0.117,   0.032,  0.686]
    project.data['const']['usvlrecovlt50']  = [0.111,   0.047,  0.563]

    # Remove old constants
    project.data['const'].pop('deathtreat', None)
    project.data['const'].pop('progusvl', None)
    project.data['const'].pop('recovgt500', None)
    project.data['const'].pop('recovgt350', None)
    project.data['const'].pop('recovgt200', None)
    project.data['const'].pop('recovgt50', None)
    project.data['const'].pop('recovusvl', None)
    project.data['const'].pop('stoppropcare', None)

    # Update parameters
    for ps in project.parsets.values():
        for pd in ps.pars:
            
            # Remove old parameters
            pd.pop('biofailure', None)
            pd.pop('deathtreat', None)
            pd.pop('immediatecare', None)
            pd.pop('progusvl', None)
            pd.pop('recovgt500', None)
            pd.pop('recovgt350', None)
            pd.pop('recovgt200', None)
            pd.pop('recovgt50', None)
            pd.pop('recovusvl', None)
            pd.pop('restarttreat', None)
            pd.pop('stoppropcare', None)
            pd.pop('stoprate', None)

            # Add new parameters
            pd['deathsvl']          = op.Constant(0.23,    limits=(0,'maxmeta'),       by='tot', auto='const', fittable='const', name='Relative death rate on suppressive ART (unitless)',                 short='deathsvl')
            pd['deathusvl']         = op.Constant(0.4878,  limits=(0,'maxmeta'),       by='tot', auto='const', fittable='const', name='Relative death rate on unsuppressive ART (unitless)',               short='deathusvl')
            pd['svlrecovgt350']     = op.Constant(2.2,     limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Treatment recovery into CD4>500 (years)',                           short='svlrecovgt350')
            pd['svlrecovgt200']     = op.Constant(1.42,    limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Treatment recovery into CD4>350 (years)',                           short='svlrecovgt200')
            pd['svlrecovgt50']      = op.Constant(2.14,    limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Treatment recovery into CD4>200 (years)',                           short='svlrecovgt50')
            pd['svlrecovlt50']      = op.Constant(0.66,    limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Treatment recovery into CD4>50 (years)',                            short='svlrecovlt50')
            pd['treatfail']         = op.Constant(0.16,    limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Treatment failure rate',                                            short='treatfail')
            pd['treatvs']           = op.Constant(0.2,     limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Time after initiating ART to achieve viral suppression (years)',    short='treatvs')
            pd['usvlproggt500']     = op.Constant(0.026,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Progression from CD4>500 to CD4>350 on unsuppressive ART',          short='usvlproggt500')
            pd['usvlproggt350']     = op.Constant(0.1,     limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Progression from CD4>350 to CD4>200 on unsuppressive ART',          short='usvlproggt350')
            pd['usvlproggt200']     = op.Constant(0.162,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Progression from CD4>200 to CD4>50 on unsuppressive ART',           short='usvlproggt200')
            pd['usvlproggt50']      = op.Constant(0.09,    limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Progression from CD4>50 to CD4<50 on unsuppressive ART',            short='usvlproggt50')
            pd['usvlrecovgt350']    = op.Constant(0.15,    limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Recovery from CD4>350 to CD4>500 on unsuppressive ART',             short='usvlrecovgt350')
            pd['usvlrecovgt200']    = op.Constant(0.053,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Recovery from CD4>200 to CD4>350 on unsuppressive ART',             short='usvlrecovgt200')
            pd['usvlrecovgt50']     = op.Constant(0.117,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Recovery from CD4>50 to CD4>200 on unsuppressive ART',              short='usvlrecovgt50')
            pd['usvlrecovlt50']     = op.Constant(0.111,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Recovery from CD4<50 to CD4>50 on unsuppressive ART',               short='usvlrecovlt50')

            # Add transitions matrix
            pd['fromto'], pd['transmatrix'] = op.loadtranstable(npops=project.data['npops'])
            
            # Convert rates to durations
            for transitkey in ['agetransit','risktransit']:
                for p1 in range(array(pd[transitkey]).shape[0]):
                    for p2 in range(array(pd[transitkey]).shape[1]):
                        thistrans = pd[transitkey][p1][p2]
                        if thistrans>0 and thistrans<1.0: pd[transitkey][p1][p2] = 1./thistrans # Invert if nonzero and also if it's a small rate (otherwise, assume it somehow got converted already)
            
            # Convert more rates to transitions
            for key in ['progacute', 'proggt500', 'proggt350', 'proggt200', 'proggt50']:
                pd[key].y = 1./pd[key].y # Invert
            

        # Rerun calibrations to update results appropriately
        if dorun: project.runsim(ps.name)

    return None


def makepropsopt(project, **kwargs):
    """
    Migration between Optima 2.1 and 2.1.1.
    """
    keys = ['propdx', 'propcare', 'proptx', 'propsupp', 'proppmtct']
    for key in keys:
        fullkey = 'opt'+key
        if fullkey not in project.data.keys():
            if key in project.data.keys():
                project.data[fullkey] = project.data.pop(key)
            else:
                raise op.OptimaException('Key %s not found, but key %s not found either' % (fullkey, key))
    return None


def addalleverincare(project, **kwargs):
    """
    Migration between Optima 2.1.1 and 2.1.2.
    """
    ps = project.settings
    ps.allevercare    = cat([ps.care, ps.usvl, ps.svl, ps.lost]) # All people EVER in care
    return None


def removenumcircdata(project, **kwargs):
    """
    Migration between Optima 2.1.2 and 2.1.3.
    """
    project.data.pop('numcirc',None)        
    return None


def removepopchardata(project, **kwargs):
    """
    Migration between Optima 2.1.3 and 2.1.4.
    """
    project.data['pops'].pop('sexworker',None)        
    project.data['pops'].pop('injects',None)        
    return None

def addaidsleavecare(project, **kwargs):
    """
    Migration between Optima 2.1.4 and 2.1.5.
    """
    short = 'aidsleavecare'
    copyfrom = 'leavecare'
    kwargs['by'] = 'tot'
    kwargs['name'] = 'AIDS loss to follow-up rate (per year)'
    kwargs['dataname'] = 'Percentage of people with CD4<200 lost to follow-up (%/year)'
    kwargs['datashort'] = 'aidsleavecare'
    kwargs['t'] = op.odict([('tot',array([2000.]))])
    kwargs['y'] = op.odict([('tot',array([0.01]))])
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    return None


def addaidslinktocare(project, **kwargs):
    """
    Migration between Optima 2.1.5 and 2.1.6.
    """
    short = 'aidslinktocare'
    copyfrom = 'linktocare'
    kwargs['by'] = 'tot'
    kwargs['name'] = 'Average time taken to be linked to care for people with CD4<200 (years)'
    kwargs['dataname'] = 'Average time taken to be linked to care for people with CD4<200 (years)'
    kwargs['datashort'] = 'aidslinktocare'
    kwargs['t'] = op.odict([('tot',array([2000.]))])
    kwargs['y'] = op.odict([('tot',array([0.01]))])
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    if not hasattr(project.settings, 'dxnotincare'):
        project.settings.dxnotincare = cat([project.settings.dx,project.settings.lost])
    return None


def adddataend(project, **kwargs):
    """
    Migration between Optima 2.1.6 and 2.1.7.
    """
    if not hasattr(project.settings, 'dataend'):
        if hasattr(project, 'data'):
            project.settings.dataend = project.data['years'][-1]
        else: project.settings.dataend = project.settings.end
    return None


def fixsettings(project, resetversion=True, **kwargs):
    """
    Migration between Optima 2.1.7 and 2.1.8.
    """
    ## Make sure settings is up to date
    settingslist = ['dt', 'start', 'now', 'dataend', 'safetymargin', 'eps', 'forcepopsize', 'transnorm'] # Keep these from the old settings object
    oldsettings = {}
    
    # Pull out original setting
    for setting in settingslist: 
        try: oldsettings[setting] = getattr(project.settings, setting) # Try to pull out the above settings...
        except: pass # But don't worry if they don't exist
    
    project.settings = op.Settings() # Completely refresh -- NOTE, will mean future migrations to settings aren't necessary!
    
    # Replace with original settings
    for settingkey,settingval in oldsettings.items(): 
        setattr(project.settings, settingkey, settingval) 

    return None


def addoptimscaling(project, **kwargs):
    """
    Migration between Optima 2.1.8 and 2.1.9.
    """
    ## New attribute for new feature
    for optim in project.optims.values():
        if 'budgetscale' not in optim.objectives.keys():
            optim.objectives['budgetscale'] = [1.]
    return None


def addpropsandcosttx(project, **kwargs):
    """
    Migration between Optima 2.1.9 and 2.1.10.
    """
    short = 'costtx'
    copyfrom = 'numtx'
    kwargs['by'] = 'tot'
    kwargs['name'] = 'Unit cost of treatment'
    kwargs['dataname'] = 'Unit cost of treatment'
    kwargs['datashort'] = 'costtx'
    kwargs['coverage'] = None
    kwargs['auto'] = 'no'
    kwargs['fittable'] = 'no'
    kwargs['limits'] = (0, 'maxpopsize')
    kwargs['t'] = op.odict([('tot',array([op.Settings().now]))])
    kwargs['y'] = op.odict([('tot',array([1.]))]) # Setting to a trivial placeholder value
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)

    short = 'fixpropdx'
    copyfrom = 'deathacute'
    kwargs['name'] = 'Year to fix PLHIV aware of their status'
    kwargs['dataname'] = 'Year to fix PLHIV aware of their status'
    kwargs['datashort'] = 'fixpropdx'
    kwargs['fittable'] = 'year'
    kwargs['y'] = 2100
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)

    short = 'fixpropcare'
    copyfrom = 'fixpropdx'
    kwargs['name'] = 'Year to fix diagnosed PLHIV in care'
    kwargs['dataname'] = 'Year to fix diagnosed PLHIV in care'
    kwargs['datashort'] = 'fixpropcare'
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)

    short = 'fixproptx'
    copyfrom = 'fixpropdx'
    kwargs['name'] = 'Year to fix PLHIV in care on treatment'
    kwargs['dataname'] = 'Year to fix PLHIV in care on treatment'
    kwargs['datashort'] = 'fixproptx'
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    
    short = 'fixproppmtct'
    copyfrom = 'fixpropdx'
    kwargs['name'] = 'Year to fix pregnant women and mothers on PMTCT'
    kwargs['dataname'] = 'Year to fix pregnant women and mothers on PMTCT'
    kwargs['datashort'] = 'fixproppmtct'
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)

    short = 'fixpropsupp'
    copyfrom = 'fixpropdx'
    kwargs['name'] = 'Year to fix people on ART with viral suppression'
    kwargs['dataname'] = 'Year to fix people on ART with viral suppression'
    kwargs['datashort'] = 'fixpropsupp'
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    
    return None




def redoparameters(project, die=True, **kwargs):
    """
    Migration between Optima 2.1.10 and 2.2 -- update the way parameters are handled.
    """
    
    verbose = 0 # Usually fine to ignore warnings
    if verbose>1:
        print('\n\n\nRedoing parameters...\n\n')
    
    # Loop over all parsets
    for ps in project.parsets.values():
        oldpars = ps.pars[0]
        tmpdata = op.dcp(project.data)
        for key,val in tmpdata['const'].items(): tmpdata[key] = val # Parameters were moved from 'const' to main data
        newpars = op.makepars(data=tmpdata, verbose=verbose, die=die) # Remake parameters using data, forging boldly ahead come hell or high water
        
        oldparnames = oldpars.keys()
        newparnames = newpars.keys()
        matchingnames = [parname for parname in oldparnames if parname in newparnames] # Find matches only
        if verbose:
            newonly = list(set(newparnames) - set(oldparnames))
            oldonly = list(set(oldparnames) - set(newparnames))
            if len(oldonly): print('The following parameters are old and not processed: %s' % oldonly)
            if len(newonly): print('The following parameters are new and not processed: %s' % newonly)
        
        # Loop over everything else
        for parname in matchingnames: # Keep going until everything is dealt with in both
            if verbose>1: print('Working on %s' % parname)
            
            # These can all be copied directly
            if parname in op._parameters.generalkeys+op._parameters.staticmatrixkeys: 
                if verbose>1: print('    Directly copying %s' % parname)
                newpars[parname] = oldpars[parname]
            
            # These require a bit more work
            else:
                # Re-populate as many attributes as possible
                for attr in oldpars[parname].__dict__.keys():
                    if hasattr(newpars[parname], attr):
                        oldattr = getattr(oldpars[parname], attr)
                        setattr(newpars[parname], attr, oldattr)
                        if verbose>2: print('     Set %s' % attr)
                
                # Handle specific changes
                if isinstance(newpars[parname], op.Metapar): # Get priors right
                    newpars[parname].prior = op.odict()
                    for popkey in newpars[parname].keys():
                        newpars[parname].prior[popkey] = op.Dist() # Initialise with defaults
                        newpars[parname].prior[popkey].pars *= newpars[parname].y[popkey]
                if isinstance(newpars[parname], op.Constant): # Get priors right, if required
                    if all(newpars[parname].prior.pars==op.Dist().pars): # See if defaults are used
                        newpars[parname].prior.pars *= newpars[parname].y # If so, rescale
                elif isinstance(newpars[parname], op.Popsizepar): # Messy -- rearrange object
                    newpars['popsize'].i = op.odict()
                    newpars['popsize'].e = op.odict()
                    for popkey in oldpars['popsize'].p.keys():
                        newpars['popsize'].i[popkey] = oldpars['popsize'].p[popkey][0]
                        newpars['popsize'].e[popkey] = oldpars['popsize'].p[popkey][1]
                elif isinstance(newpars[parname], op.Yearpar): # y attribute is renamed t
                    newpars[parname].t = oldpars[parname].y
                else: # Nothing to do
                    if verbose>2: print('  Nothing special to do with %s' % parname)
                
        # Just a bug I noticed -- I think the definition of this parameter got inverted at some point
        resetleavecare = False
        for key in newpars['leavecare'].y:
            for i,val in enumerate(newpars['leavecare'].y[key]):
                if val>0.5:
                    newpars['leavecare'].y[key][i] = 0.2
        if verbose and resetleavecare: print('Leave care rate seemed too high (%0.1f), resetting to 0.2' % (val))
        
        ps.pars = newpars # Keep the new version
    
    return None



def redovlmon(project, **kwargs):
    """
    Migration between Optima 2.2 and 2.2.1 -- update the VL monitoring parameter
    """
    
    requiredvldata = [2.0, 1.5, 2.5]
    oldvldata = op.dcp(project.data['freqvlmon'][0][-1]) # Get out old VL data -- last entry
    if isnan(oldvldata): oldvldata = requiredvldata[0]/2. # No data? Assume coverage of 50%
    project.data['numvlmon'] = [[oldvldata*project.data['numtx'][0][j] for j in range(len(project.data['numtx'][0]))]] # Set new value
    
    project.data['const']['requiredvl'] = requiredvldata
    
    removeparameter(project, short='freqvlmon', datashort='freqvlmon')
    for key,progset in project.progsets.items():
        if 'freqvlmon' in progset.covout.keys():
            msg = 'Project includes a program in programset "%s" that affects "freqvlmon", but this parameter has been removed' % key
            project.addwarning(msg)
    
    short = 'numvlmon'
    copyfrom = 'numtx'
    kwargs['name'] = 'Viral load monitoring (number/year)'
    kwargs['dataname'] = 'Viral load monitoring (number/year)'
    kwargs['datashort'] = 'numvlmon'
    kwargs['t'] = op.odict([('tot',op.getvaliddata(project.data['years'], project.data['numvlmon'][0]))])
    kwargs['y'] = op.odict([('tot',op.getvaliddata(project.data['numvlmon'][0]))])
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    
    short = 'requiredvl'
    copyfrom = 'treatvs'
    kwargs['name'] = 'Number of VL tests recommended per person per year'
    kwargs['dataname'] = 'Number of VL tests recommended per person per year'
    kwargs['datashort'] = 'requiredvl'
    kwargs['y'] = requiredvldata[0]
    kwargs['prior'] = op.Dist(dist='uniform', pars=(requiredvldata[1], requiredvldata[2]))
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)

    return None
        

def addprojectinfo(project, verbose=2, **kwargs):
    ''' Add project info to resultsets so they can be loaded '''
    
    for item in project.parsets.values()+project.progsets.values()+project.optims.values()+project.results.values():
        item.projectref = op.Link(project)
        try:    del item.project
        except: op.printv('No project attribute found for %s' % item.name, 3, verbose)
            
    for result in project.results.values():
        result.projectinfo = project.getinfo()
    
    return None


def redoparamattr(project, **kwargs):
    ''' Change the names of the parameter attributes, and change transnorm from being a setting to being a parameter '''
    
    # Change parameter attributes
    for ps in project.parsets.values():
        for par in ps.pars:
            if isinstance(par, op.Par): # Loop over the parameters and adjust their properties
                for attr in ['dataname', 'datashort', 'auto', 'visible', 'proginteract', 'coverage']: 
                    delattr(par, attr) # Remove outdated properties
    
    # Add transnorm
    short = 'transnorm'
    copyfrom = 'transmfi'
    kwargs['name'] = 'Normalization factor for transmissibility'
    kwargs['y'] = project.settings.transnorm
    kwargs['fromdata'] = 0
    kwargs['limits'] = (0, 'maxmeta')
    kwargs['prior'] = op.Dist(dist='uniform', pars=project.settings.transnorm*array([ 0.9,  1.1]))
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    
    return None


def removespreadsheet(project, **kwargs):
    ''' Remove the binary spreadsheet (it's big, and unnecessary now that you can write data) '''
    delattr(project, 'spreadsheet')
    return None


def addagetopars(project, **kwargs):
    ''' Make sure age is part of the pars object '''
    for ps in project.parsets.values():
        ps.pars['age'] = array(project.data['pops']['age'])
    return None


def redotranstable(project, **kwargs):
    ''' Redo how the transition table is handled and add infinite money '''
    
    # Refresh settings since potentially bunged when the transition matrix is reloaded
    fixsettings(project, resetversion=False, **kwargs)
    
    # Add transitions matrix
    for ps in project.parsets.values():
        ps.pars['fromto'], ps.pars['transmatrix'] = op.loadtranstable(npops=project.data['npops'])
        ps.pars.pop('rawtransit', None) # If it's really old, it won't actually have this
    
    # Even though fixed by fixsettings above, just make it explicit that we're adding this as well
    project.settings.infmoney = 1e10
    
    return None


def addtimevarying(project, **kwargs):
    ''' Update optimization objects to include time-varying settings '''
    for opt in project.optims.values():
        opt.tvsettings = op.defaulttvsettings()
    for parset in project.parsets.values():
        try:    assert(op.isnumber(parset.start))
        except: parset.start = project.settings.start
        try:    assert(op.isnumber(parset.end))
        except: parset.end = project.settings.end
    return None


def addtreatbycd4(project, **kwargs):
    ''' Update project to include a treatbycd4 setting '''
    project.settings.treatbycd4 = True
    return None


def removecosttx(project, **kwargs):
    """
    Migration between Optima 2.6.7 and 2.6.8: removes costtx parameter
    """
    removeparameter(project, short='costtx', datashort='costtx')
    return None


def addrelhivdeath(project, **kwargs):
    """
    Migration between Optima 2.6.8 and 2.6.9: add a population-dependent relative HIV death rate
    """

    short = 'hivdeath'
    copyfrom = 'force'
    kwargs['name'] = 'Relative death rate for populations (unitless)'
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    npops = len(project.data['pops']['short'])
    for ps in project.parsets.values():
        ps.pars['hivdeath'].y[:] = array([1.]*npops)
        for key in range(npops): ps.pars['hivdeath'].prior[key].pars = array([0.9, 1.1]) 
    
    return None


def addspectrumranges(project, **kwargs):
    """
    Migration between Optima 2.6.9 and 2.6.10: add ranges for optional data inputs and rename PrEP
    """
    
    # Add ranges
    optindicators = ['optpropdx','optpropcare','optproptx','optpropsupp','optproppmtct','optnumtest','optnumdiag','optnuminfect','optprev','optplhiv','optdeath','optnewtreat']
    for optind in optindicators:
        if len(project.data[optind])==1:
            tmpdata = op.dcp(project.data[optind])
            newdata = []
            newdata.append([nan]*len(project.data[optind][0])) # No data for high estimate
            newdata.append(tmpdata[0]) # Previous data for best estimate
            newdata.append([nan]*len(project.data[optind][0])) # No data for low estimate
            project.data[optind] = newdata
    
    # Rename PrEP
    for ps in project.parsets.values():
        ps.pars['prep'].name    = 'Proportion of exposure events covered by ARV-based prophylaxis'
        ps.pars['effprep'].name = 'Efficacy of ARV-based prophylaxis'
    
    return None


def circmigration(project, **kwargs):
    """
    Migration between Optima 2.6.10 and 2.6.11: add circumcision migration
    """
    
    ## Redo circ parameters
    malelist = [val for i,val in enumerate(project.data['pops']['short']) if project.data['pops']['male'][i]]
    femalelist = [val for i,val in enumerate(project.data['pops']['short']) if project.data['pops']['female'][i]]
    
    for pset in project.parsets.values():

        if pset.pars['propcirc'].by=='pop':
            pset.pars['propcirc'].by = 'mpop'
            for fpop in femalelist: 
                pset.pars['propcirc'].t.pop(fpop)
                pset.pars['propcirc'].y.pop(fpop)

        if pset.pars['numcirc'].by=='pop':
            pset.pars['numcirc'].by = 'mpop'
            for fpop in femalelist: 
                pset.pars['numcirc'].t.pop(fpop)
                pset.pars['numcirc'].y.pop(fpop)
                
        if pset.pars['birth'].by=='pop':
            pset.pars['birth'].by = 'fpop'
            for mpop in malelist: 
                pset.pars['birth'].t.pop(mpop)
                pset.pars['birth'].y.pop(mpop)
            
    return None
    

def changehivdeathname(project, **kwargs):
    """
    Change name of relative HIV-related death rate
    """
    
    for pset in project.parsets.values():
        pset.pars['hivdeath'].name = 'Relative HIV-related death rate (unitless)'
    
    return None

    
def tvtreatfail(project, **kwargs):
    """
    Migration between Optima 2.6.12 and 2.7: redo treatment failure
    """
    short = 'regainvs'
    copyfrom = 'numvlmon'
    kwargs['name'] = 'Proportion of cases with detected VL failure for which there is a switch to an effective regimen (%/year)'
    kwargs['limits'] = (0, 'maxrate')
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    for ps in project.parsets.values():
        ps.pars['regainvs'].y[:] = array([[1.]]) # Assume 100% are shifted (for backward compatability)
        ps.pars['regainvs'].t[:] = array([[2017.]]) 
    
    removeparameter(project, short='treatfail', datashort='treatfail')
    
    short = 'treatfail'
    copyfrom = 'numvlmon'
    kwargs['name'] = 'Treatment failure rate'
    kwargs['limits'] = (0, 'maxrate')
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    for ps in project.parsets.values():
        ps.pars['treatfail'].y[:] = array([[.16]]) # Assume 16% are shifted
        ps.pars['treatfail'].t[:] = array([[2017.]]) 

    return None


def addfixedattr(project, **kwargs):
    """
    Migration between Optima 2.7.1 and 2.7.2: add fixedness attribute
    """
    for ps in project.parsets.values():
        if abs(ps.pars['fixproptx'].t - 2100) < 0.1:
            ps.isfixed = False
        else: ps.isfixed = True
    return None


def addpopfactor(project, **kwargs):
    """
    Migration between Optima 2.7.2 and 2.7.3 and 2.7.4: add popfactor attribute
    """
    for progset in project.progsets.values():
        program_list = progset.programs.values()
        try:    inactive_list = progset.inactive_programs.values()
        except: inactive_list = [] # This might fail if there are no inactive programs; don't worry
        all_programs = program_list + inactive_list
        for program in all_programs:
            try:
                ccopars = program.costcovfn.ccopars # Won't exist or will be empty for e.g. fixed cost programs
                if ccopars: # Don't do anything if it's empty or None
                    if 'popfactor' not in ccopars: # Don't add it if it's already there
                        ccopars['popfactor'] = []
                        for yr in range(len(ccopars['t'])): # Give it the right number of elements
                            istuple = True
                            try: # This shouldn't fail, but it really doesn't matter if it does, so be safe
                                if op.isnumber(ccopars['saturation'][yr]) and op.isnumber(ccopars['unitcost'][yr]):
                                    istuple = False # If everything else is just a plain number, make this a plain number too
                            except:
                                pass
                            if istuple: ccopars['popfactor'].append((1.0,1.0))
                            else:       ccopars['popfactor'].append(1.0)
            except:
                pass # Don't really worry if it didn't work
    return None


def addcascadeopt(project=None, portfolio=None, **kwargs):
    '''
    Migration between Optima 2.8.2 and 2.9.0 -- for both projects and portfolios
    '''
    if project is not None:
        objectives_list = [optim.objectives for optim in project.optims.values()]
    elif portfolio is not None:
        objectives_list = [portfolio.objectives]
    else:
        raise Exception('Must supply either a project or a portfolio')
    for objectives in objectives_list:
        objectives['cascadekeys']    = ['propdiag', 'proptreat', 'propsuppressed']
        objectives['propdiag']       = 0
        objectives['proptreat']      = 0
        objectives['propsuppressed'] = 0
#        objectives.pop('keylabels') # Never used
    return None



def fixcascadeopt(project=None, portfolio=None, **kwargs):
    '''
    Migration between Optima 2.9.0 and 2.9.1 -- for both projects and portfolios -- fixes the previous migration
    '''
    if project is not None:
        objectives_list = [optim.objectives for optim in project.optims.values()]
    elif portfolio is not None:
        objectives_list = [portfolio.objectives]
    else:
        raise Exception('Must supply either a project or a portfolio')
    for objectives in objectives_list:
        objectives['keylabels'] = op.odict({ # Define key labels
                                        'death':          'Deaths', 
                                        'inci':           'New infections', 
                                        'daly':           'DALYs', 
                                        'propdiag':       'Proportion diagnosed',
                                        'proptreat':      'Proportion treated (of those diagnosed)',
                                        'propsuppressed': 'Proportion suppressed (of those treated)'})
    return None


def addprogdefault(project=None, **kwargs):
    '''
    Migration between Optima 2.9.3 and 2.9.4 -- add default values for parameters in absence of programs
    '''
    if project is not None:
        if project.parsets:
            for ps in project.parsets.values():
                for par in ps.pars.values():
                    if isinstance(par, op.Par):
                        if par.short in ['hivtest', 'aidstest', 'numtx', 'numpmtct', 'prep', 'numvlmon', 'regainvs', 'numost']:
                            par.progdefault = 0.  # For this migration, all the defaults should be zero.
                        else: par.progdefault = None
    else:
        raise Exception('Must supply a project')
    return None


def addpepreturntocare(project=None, **kwargs):
    '''
    Migration between Optima 2.9.4 and 2.10.0 -- Add PEP parameters, rename PrEP parameters, and add a return to care parameter distinct from link to care
    '''
    if project is not None:
        #rename prep pars
        # Rename PrEP
        #rename and re-add circumcision parameters
        for ps in project.parsets.values():
            ps.pars['prep'].name    = 'Proportion of exposure events covered by ARV-based pre-exposure prophylaxis'
            ps.pars['effprep'].name = 'Efficacy of ARV-based pre-exposure prophylaxis'
            ps.pars['propcirc'].name = 'Percentage of males who have been traditionally circumcised'
            ps.pars['numcirc'].name = 'Number of voluntary medical male circumcisions'
        #add PEP pars
        short = 'pep'
        copyfrom = 'prep'
        kwargs['by'] = 'pop'
        kwargs['name'] = 'Proportion of exposure events covered by ARV-based post-exposure prophylaxis'
        kwargs['dataname'] = 'Proportion of exposure events covered by ARV-based post-exposure prophylaxis'
        kwargs['datashort'] = 'pep'
        kwargs['t'] = op.odict([(pop,array([2000.])) for pop in ps.popkeys])
        kwargs['y'] = op.odict([(pop,array([0.00])) for pop in ps.popkeys])
        addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
        
        short = 'effpep'
        copyfrom = 'effprep'
        kwargs['by'] = 'tot'
        kwargs['name'] = 'Efficacy of ARV-based post-exposure prophylaxis'
        kwargs['dataname'] = 'Efficacy of ARV-based post-exposure prophylaxis'
        kwargs['datashort'] = 'effpep'
        if 't' in kwargs.keys(): kwargs.pop('t')
        kwargs['y'] = 0.73 #default efficacy value of ARV-based prophylaxis combining PrEP and PEP use, not the updated values for either to maintain project consistency
        addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
        
        #add return to care par - all values should be copied from link to care to maintain consistency
        short = 'returntocare'
        copyfrom = 'linktocare'
        kwargs['by'] = 'pop'
        kwargs['name'] = 'Average time taken to be returned to care after loss to follow-up (years)'
        kwargs['dataname'] = 'Average time taken to be returned to care after loss to follow-up (years)'
        kwargs['datashort'] = 'returntocare'
        if 't' in kwargs.keys(): kwargs.pop('t')
        if 'y' in kwargs.keys(): kwargs.pop('y')
        addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
        
        
        #add data for PEP, PrEP, and return to care
        project.data['meta']['sheets']['Sexual behavior'].append('numcirc')
        project.data['numcirc'] = [[nan]*len(project.data['years']) for _ in range(project.data['npops'])]
        project.data['meta']['sheets']['Constants'].append('effpep')
        project.data['effpep'] = [0.73, 0.65, 0.80] #default efficacy value of ARV-based prophylaxis combining PrEP and PEP use, not the updated values for either to maintain project consistency
        project.data['meta']['sheets']['Testing & treatment'].append('pep')
        project.data['pep'] = [[nan]*len(project.data['years']) for _ in range(project.data['npops'])]
        project.data['meta']['sheets']['Cascade'].append('returntocare')
        project.data['returntocare'] = [[nan]*len(project.data['years']) for _ in range(project.data['npops'])]
        
        
        #Rename year to fix parameters to clarify their use
        for ps in project.parsets.values():
            ps.pars['fixpropdx'].name    = 'Year to fix proportion of PLHIV aware of their status'
            ps.pars['fixpropcare'].name  = 'Year to fix proportion of diagnosed PLHIV in care'
            ps.pars['fixproptx'].name    = 'Year to fix proportion of PLHIV in care on treatment'
            ps.pars['fixpropsupp'].name  = 'Year to fix proportion of people on ART with viral suppression'
            ps.pars['fixproppmtct'].name = 'Year to fix proportion of pregnant women and mothers on PMTCT'
        
    else:
        raise Exception('Must supply a project')
    return None


def updatedisutilities(project=None, **kwargs):
    '''
    Migration between Optima 2.10.0 and 2.10.1 -- Update disutility weights for DALYs from GBD 2010 to GBD 2019
    '''
    if project is not None:
        #update disutility weights in the data
        project.data['disutilacute'] = [0.181, 0.121, 0.249]
        project.data['disutilgt500'] = [0.010, 0.007, 0.014]
        project.data['disutilgt350'] = [0.025, 0.017, 0.035]
        project.data['disutilgt200'] = [0.081, 0.055, 0.107]
        project.data['disutilgt50']  = [0.289, 0.128, 0.499]
        project.data['disutillt50']  = [0.582, 0.406, 0.743]
        project.data['disutiltx']    = [0.078, 0.052, 0.111]
        
        #update disutility weights in each parset - both the parset value and the prior for uncertainty
        for ps in project.parsets.values():
            for parname in ['disutilacute', 'disutilgt500', 'disutilgt350', 'disutilgt200', 'disutilgt50', 'disutillt50', 'disutiltx']:
                ps.pars[parname].y = project.data[parname][0]
                ps.pars[parname].prior.pars[0] = project.data[parname][1]
                ps.pars[parname].prior.pars[1] = project.data[parname][2]
            
    else:
        raise Exception('Must supply a project')
    return None


def updateprepconstants(project=None, **kwargs):
    '''
    Migration between Optima 2.10.1 and 2.10.2 -- Actually force prep/pep constants to be updated
    WARNING: this will likely change calibration restults as the result of changing treatment efficacy as well as prep/pep
    '''
    if project is not None:
        #update data values
        project.data['effpep'] = [0.73, 0.65, 0.80] #default efficacy value of ARV-based prophylaxis combining PrEP and PEP use, not the updated values for either to maintain project consistency
        project.data['effprep'] = [0.95, 0.92, 0.97] #default efficacy value of ARV-based prophylaxis combining PrEP and PEP use, not the updated values for either to maintain project consistency
        project.data['efftxsupp'] = [1.0, 0.92, 1.0] #default efficacy value of ARV-based prophylaxis combining PrEP and PEP use, not the updated values for either to maintain project consistency
        
        #Update parameter values in each parset
        for ps in project.parsets.values():
            ps.pars['effpep'].y   = 0.73
            ps.pars['effpep'].prior.pars = array([0.65, 0.80])
            ps.pars['effprep'].y  = 0.95
            ps.pars['effprep'].prior.pars = array([0.92, 0.97])
            ps.pars['efftxsupp'].y  = 1.0
            ps.pars['efftxsupp'].prior.pars = array([0.92, 1.0])
        
    else:
        raise Exception('Must supply a project')
    return None


def addageingrates(project=None, **kwargs):
    '''
    Migration between Optima 2.10.2 and 2.10.3
    -- Add an ageing table to allow ageing to occur by year to reflect non-uniform population distributions
    '''
    if project is not None:
        #update data values
        for ps in project.parsets.values():
            #add a parameter for ageing rate
            short = 'agerate'
            copyfrom = 'death'
            kwargs['by'] = 'pop'
            kwargs['name'] = 'Percentage of people who age into the next age category per year'
            kwargs['dataname'] = 'Ageing rate (per year)'
            kwargs['datashort'] = 'agerate'
            kwargs['t'] = op.odict([(pop,array([2000.])) for pop in ps.popkeys])
            kwargs['y'] = op.odict([(pop,array([1./(popages[1]-popages[0]+1)])) for pop, popages in zip(ps.popkeys, ps.pars['age'])])
            addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)

            #Also neeed to adjust the agetransit parameter to be proportions rather than absolute value
            for rn, row in enumerate(ps.pars['agetransit']):
                if sum(ps.pars['agetransit'][rn])>0:
                    ps.pars['agetransit'][rn] = ps.pars['agetransit'][rn]/sum(ps.pars['agetransit'][rn])
        
        #add data for PEP, PrEP, and return to care
        project.data['meta']['sheets']['Other epidemiology'].append('agerate')
        project.data['agerate'] = [[1./(popages[1]-popages[0]+1)] for popages in project.data['pops']['age']]
        
    else:
        raise Exception('Must supply a project')
    return None


def partlinearccopars(project=None, **kwargs):
    '''
    Migration between Optima 2.10.3 and 2.10.4
    -- Update cost-coverage curves to be linear to saturation_low then non-linear to saturation high
    '''
    if project is not None:
        for ps in project.progsets.values():
            for prog in ps.programs.values():
                #for each program convert saturation values (lower, upper) to (0, average(lower, upper)) to maintain consistent results with partially linear cost-coverage curves
                if prog.costcovfn.ccopars:
                        prog.costcovfn.ccopars['saturation'] = [(0., mean(sat)) for sat in prog.costcovfn.ccopars['saturation']]
    else:
        raise Exception('Must supply a project')
    return None

# def renameunaidspars(project=None, **kwawrgs):
#     '''
#     Migration between Optima 2.10.4 and 2.10.5
#     -- Rename optional indicators to align with UNAIDS terminology
#     -	PLHIV aware of their status (%)  -> Percent of people living with HIV who know their status
#     -	Diagnosed PLHIV in care (%)  -> Percent of people who know their status who are retained in care
#     -	PLHIV in care on treatment (%) -> Percent of people who know their status who are on ART (note this was always used in model output comparisons as % diagnosed/%treated, so this renaming is an actual correction!)
#     -	Pregnant women on PMTCT (%) -> Coverage of pregnant women who receive ARV for PMTCT
#     -	People on ART with viral suppression (%)  -> Percent of people on ART who achieve viral suppression
#     '''
#     if project is not None:
#         #No need to rename anything in data (never saved!)
#         #May need to rename the output/results long names in all result sets, might have other side effects though?            
#     else:
#         raise Exception('Must supply a project')
#     return None
    
#     return None

def removerequiredvl(project=None, **kwwargs):
    '''
    Migration between Optima 2.10.5 and 2.10.6 -- remove the "required VL tests" parameter - as the implementation doesn't match the interpretation
    The model uses this to determine the proportion of treatment failures identified every timestep, so this should be hardcoded as 1/dt instead
    It has been appropriate to adjust this to reflect better targeting of limited viral load testing to those most at risk of treatment failure in many countries,
    but that would be better achieved through adjustment of the metaparameter for 'numvlmon' instead, with the same overall impact.
    '''
    if project is not None:
        #First adjust the metaparameter for number of viral load tests given to account for better targeting of viral load tests
        for ps in project.parsets.values():
            ps.pars['numvlmon'].m *= (1./project.settings.dt) / ps.pars['requiredvl'].y
        #Then remove the parameter from all parsets
        removeparameter(project=project, short='requiredvl', data='requiredvl')
    else:
        raise Exception('Must supply a project')
    return None

def addmetapars(project=None, **kwargs):
    '''
    Migration between Optima 2.10.6 and 2.10.7 
    
    First fix where legacy projects have some priors as dicts instead of op.Dists and that causes errors (e.g. with updatepriors) - do that here
    
    -- Add meta parameter initcd4weight to weight initialization toward earlier/later stage infections
        This setting has a default value of 1. which will initialize based on average duration in each stage of infection
        Values <1 mean the initialization will be weighted toward high CD4 counts and especially acute infections for people who are not on treatment [early stage epidemics]
        Values >1 mean the initialization will be weighted toward low CD4 counts and especially CD4<50 infections for people who are not on treatment [early stage epidemics]
    -- Migrate binary project setting forcepopsize to a parameter
    -- Migrate binary project setting treatbycd4 to a parameter representing year in which treatment prioritization changes from by cd4 count to eligibility for all
    -- Add meta parameter 'rrcomorbiditydeathtx' (by time and population) to modify relative death rates for people on ART (e.g. improved treatment of comorbidities)
    -- Add meta parameter 'relhivbirth' to capture the relative likelihood that a female with HIV gives birth relative to the overall birth rate
    '''
    if project is not None:
        #Calculate what the new paramater values should be consistent with as previously defined
        if hasattr(project.settings, 'forcepopsize'):
            forcepopsize = 1 if project.settings.forcepopsize else 0
            delattr(project.settings, 'forcepopsize')
        else:
            forcepopsize = 0 #default
        if hasattr(project.settings, 'treatbycd4'):
            allcd4eligibletx = 2100 if project.settings.treatbycd4 else 1900
            delattr(project.settings, 'treatbycd4')
        else:
            allcd4eligibletx = 1900 #default (all CD4 equally eligible for treatment all years
        
        newpars = {'forcepopsize':     {'copyfrom': 'transnorm', 'name': 'Force all population sizes to match initial value with exponential growth curve',
                                        'y': forcepopsize, 'limits': (0,1)},
                   'allcd4eligibletx': {'copyfrom': 'fixpropdx', 'name': 'Return to care rate (per year)', 
                                        't': allcd4eligibletx, 'limits': (0, 'maxyear')},
                   'initcd4weight':    {'copyfrom': 'transnorm', 'name': 'Weighting for initialization where low values represent early stage epidemics', 
                                        'y': 1., 'limits': (0, 'maxmeta')},
                   'rrcomorbiditydeathtx':     {'copyfrom': 'death', 'name': 'Relative risk of death rate on ART (unitless, time-based adjustment for treatment of comorbidities)', 
                                        'limits': (0, 'maxmeta')}, #set y values below
                   'relhivbirth':      {'copyfrom': 'transnorm', 'name': 'Relative likelihood that females with HIV give birth', 
                                        'y': 1, 'limits': (0,'maxmeta')},
                   }
        
        #Fix any outdated priors that were defined as dicts instead of Dists in the project before copying parameters
        for ps in project.parsets.values():
            for par in ps.pars.values():
                # Handle specific changes
                if isinstance(par, op.Metapar): # Should be a dict of Dists (one per population)
                    for popkey in par.keys():
                        if isinstance(par.prior[popkey], dict): 
                            par.prior[popkey] = op.Dist(**par.prior[popkey])
                elif isinstance(par, (op.Constant, op.Timepar, op.Popsizepar)): # Should be a single Dist
                    if isinstance(par.prior, dict):
                        par.prior = op.Dist(**par.prior)
                
                if hasattr(par, 'prior'): #update all priors while there?
                    par.updateprior()
        
        #Now actually add the new parameters
        for parname, parkwargs in newpars.items():

            addparameter(project=project, short=parname, **parkwargs)
            par = ps.pars[parname]
            for ps in project.parsets.values():               
                if parname == 'rrcomorbiditydeathtx':
                    for pop in par.y.keys():
                        par.y[pop] = array([1.])
                
                #We don't actually want to sample these by default: set the priors to have no sampling range
                if isinstance(par, op.Metapar): # Should be a dict of Dists (one per population)
                    for popkey in par.keys():
                        par.prior[popkey].pars = (par.y[popkey], par.y[popkey])
                elif isinstance(par, (op.Constant, op.Timepar, op.Popsizepar)): # Should be a single Dist
                    par.prior.pars = (par.y, par.y)
                        
    else:
        raise Exception('Must supply a project')
    return None

def adjustreturnpar(project=None, **kwargs):
    '''
    Migration between Optima 2.10.7 and 2.10.8 
    
    - Make return to care a rate instead of a duration to facilitate more accurate program impacts
    - Includes simplification of program coverage logic
    '''
    if project is not None:
        dt = project.settings.dt
        eps = project.settings.eps
        for ps in project.parsets.values():
            ps.pars['returntocare'].name = 'Return to care rate (per year)'
            ps.pars['returntocare'].dataname = 'Percentage of people lost to follow-up who are returned to care per year (%/year)'
            for popkey in ps.pars['returntocare'].y.keys():
                ps.pars['returntocare'].y[popkey] = array([(1-exp(-dt/max(eps, yrval)))/dt for yrval in ps.pars['returntocare'].y[popkey]])
            ps.pars['returntocare'].updateprior()
            
        #also need to invert values in any covouts for returntocare
        for pg in project.progsets.values():
            if 'returntocare' in pg.covout.keys():
                for pop in pg.covout['returntocare'].keys():
                    for impact in pg.covout['returntocare'][pop].ccopars.keys():
                        if impact != 't': #impact includes 'intercept' and all populations, but not t!
                            pg.covout['returntocare'][pop].ccopars[impact] = [((1-exp(-dt/max(eps, high)))/dt, (1-exp(-dt/max(eps, low)))/dt) for low, high in pg.covout['returntocare'][pop].ccopars[impact]]                          
            
    return None

def fixmanfitsettings(project=None, **kwargs):
    '''
    Migration between Optima 2.10.10 and 2.10.11 
    
    - Adjust manual calibration flags for added parameters
    '''
    if project is not None:            
        for ps in project.parsets.values():
            ps.pars['allcd4eligibletx'].manual = 'year'
            ps.pars['initcd4weight'].manual    = 'const'
            ps.pars['forcepopsize'].manual     = 'const'
            ps.pars['relhivbirth'].manual      = 'const'
            ps.pars['rrcomorbiditydeathtx'].manual = 'no'
    return None

def popgrowthoptions(project=None, **kwargs):
    '''
    Migration between Optima 2.10.11 and 2.10.12 
    
    - Add extra attributes to Popsizepar parameters to capture the full data values
    - Before .start year use interpolated pop sizes from the databook
    - From .start year use exponential growth from the last data pop size
    '''
    if project is not None:        
        for ps in project.parsets.values():
            par = ps.pars['popsize']
            
            par.y = op.odict()
            par.t = op.odict() 
            par.start = op.odict()
            for popind, pop in enumerate(par.e.keys()):
                #as if loading data into y and t values
                blh = 0 #best-low-high = 0-1-2
                par.start[pop] = op.dcp(ps.start)
                
                popsizedata = project.data['popsize'][blh][popind]
                if len(popsizedata)==1: #it's an assumption (very uncommon)
                    popsizedata = array(popsizedata*len(project.data['years']))
                    
                par.y[pop] = op.sanitize(popsizedata) # Store each extant value
                par.t[pop] = array(project.data['years'])[~isnan(popsizedata)] # Store each year
                
                #check if a start year value exists
                if not ps.start in par.t[pop]: #add an initial value dummy 'data' point
                    par.y[pop] = append([par.i[pop]], par.y[pop])
                    par.t[pop] = append([ps.start], par.t[pop])
                else: #reset the first value to the previous .i value for consistency
                    par.y[pop][0] = array([par.i[pop]])
                    
            del(ps.pars['popsize'].i)
    return None

def migrationmigration(project=None, **kwargs):
    '''
    Migration between Optima 2.10.12 and 2.10.13 
    
    This migration adds migration parameters (all of which are Timepars per population)
    - propemigrate, numimmigrate, immihivprev, immipropdiag
    Also included with this version update are changes to the model code to implement migration
    '''
    if project is not None:        
        for ps in project.parsets.values():
            
            newpars = {'propemigrate': {'copyfrom': 'death', 'name': 'Percentage of people who emigrate per year',
                                        'limits': (0,'maxrate')},
                   'numimmigrate': {'copyfrom': 'death', 'name': 'Number of people who immigrate into population per year', 
                                        'limits': (0, 'maxpopsize')},
                   'immihivprev':  {'copyfrom': 'stiprev', 'name': 'HIV prevalence of immigrants into population per year', 
                                        'limits': (0, 1)},
                   'immipropdiag': {'copyfrom': 'stiprev', 'name': 'Proportion of people living with HIV who immigrate who are diagnosed prior to arrival', 
                                        'limits': (0, 1)},
                   }
            
            #Now actually add the new parameters
            for parname, parkwargs in newpars.items():
                addparameter(project=project, short=parname, **parkwargs)
                par = ps.pars[parname]
                for ps in project.parsets.values():
                    for pop in par.y.keys():
                        par.t[pop] = array([ps.start])
                        par.y[pop] = array([0.])
            
    return None


def addsexinjmtctsettings(project=None, **kwargs):
    '''
    Migration between Optima 2.10.13 and 2.10.14

    This migration adds settings: sex, inj and mtct which are the indices of these methods of transmission
    in a causes matrix, as well as the names of and number of methods of transmission
    
    Warning: breaks saved results (fixed in 2.10.6 migration)
    '''
    if project is not None and project.settings is not None:
        base_settings = op.Settings()
        project.settings.heterosexsex = base_settings.heterosexsex
        project.settings.homosexsex = base_settings.homosexsex
        project.settings.inj = base_settings.inj
        project.settings.mtct = base_settings.mtct
        project.settings.nmethods = base_settings.nmethods
        project.settings.methodnames = base_settings.methodnames
        project.settings.advancedtracking = base_settings.advancedtracking
    return None

def fixmoremanfitsettings(project=None, **kwargs):
    '''
    Migration between Optima 2.10.14 and 2.10.15 
    
    - Adjust manual calibration flags for added parameters
    '''
    if project is not None:            
        for ps in project.parsets.values():
            ps.pars['propemigrate'].manual = 'meta'
            ps.pars['numimmigrate'].manual = 'meta'
            ps.pars['immihivprev'].manual  = 'meta'
            ps.pars['immipropdiag'].manual = 'meta'
    return None

def clearuntrackedresults(project=None, **kwargs):
    '''
    Migration between Optima 2.10.15 and 2.10.16 
    
    - If results were not updated a couple of migrations previously then remove them now and need to rerun
    - This update also includes adding advanced tracking plots to the FE
    '''
    if project is not None:
        for res in project.results.values():
            if not hasattr(res, 'advancedtracking'): #if anything wasn't migrated previously just clear the result and user will rerun, migration is complex otherwise
                project.results = op.odict()
                break
    return None

def addallconstraintsoptim(project=None, **kwargs):
    '''
    Migration between Optima 2.11.3 and 2.11.4
    - Add proporigconstraints and absconstraints to the Optims in the project
    '''
    if project is not None:
        for optim in project.optims.values():
            if not hasattr(optim, 'constraints'):         optim.constraints         = None  # Should already have constraints but check anyway
            if not hasattr(optim, 'proporigconstraints'): optim.proporigconstraints = None
            if not hasattr(optim, 'absconstraints'):      optim.absconstraints      = None
    return None

def addinsertonlyacts(project=None, **kwargs):
    '''
    Migration between Optima 2.11.4 and 2.12.0
    - actsreg, actscas, actscom are now only insertive acts, so we add a attribute insertiveonly to pars['actsreg'] etc
    '''
    if project is not None:
        for parset in project.parsets.values():
            for parname in ['actsreg', 'actscas', 'actscom']:
                par = parset.pars[parname]
                if not hasattr(par, 'insertiveonly'):
                    par.insertiveonly = False  # Previously generated parsets don't have insertive only
    return None


def fixzeronumcircparset(project=None, **kwargs):
    '''
    Migration between Optima 2.12.0 and 2.12.1
    This undos the parset.pars['numcirc'].y[key] = array([0.0]) that used to set `numcirc` to 0
    '''
    if project is not None and project.data is not None and project.parsets.keys():
        # Based on makepars()
        orignumcirc = project.parset().pars['numcirc']
        orignumcircdict = op.dcp(orignumcirc.__dict__)
        for key in ['m', 't', 'y', 'projectversion']: orignumcircdict.pop(key, None)

        mpopkeys = [popkey for popno, popkey in enumerate(project.data['pops']['short']) if project.data['pops']['male'][popno]]

        replacementnumcirc = op.parameters.data2timepar(data=project.data, keys=mpopkeys, **orignumcircdict)

        for parset in project.parsets.values():
            allzero = all(parset.pars['numcirc'].y.values() == array([0]))
            if allzero:
                parset.pars['numcirc'] = replacementnumcirc
    return None

##########################################################################################
### REVISION MIGRATION FUNCTIONS
##########################################################################################

def parsandprograms_odictcustom(project=None, **kwargs):
    '''
        Migration between revision 0 and 1
        Convert Parameterset.pars and Programset.programs to be odict_custom, which links back to the
        Parameterset and Programset respectively
    '''
    if project is not None:
        # propagate version, then we make sure that any new parsets we add have projectversion == version
        project.parsets = op.odict_custom(project.parsets, func=project.propagateversion)
        project.parsets.func = project.checkpropagateversionlink
        project.parsets.func(project.parsets, project.parsets.keys(), project.parsets.values()) # run it once to link

        for parset in project.parsets.values():
            parset.pars = op.odict_custom(parset.pars, func=parset.propagateversion)
            parset.pars.func = parset.checkpropagateversion

        # propagate version, then we make sure that any new parsets we add have projectversion == version
        project.progsets = op.odict_custom(project.progsets, func=project.propagateversion)
        project.progsets.func = project.checkpropagateversionlink
        project.progsets.func(project.progsets, project.progsets.keys(), project.progsets.values())  # run it once to link

        for progset in project.progsets.values():
            progset.programs = op.odict_custom(progset.programs, func=progset.propagateversion)
            progset.programs.func = progset.checkpropagateversion


def updatemethodsettings(project=None, **kwargs):
    '''
        Migration between revision 3 and 4,
        Clears results and sets the new settings for methods of transmission
    '''
    if project is not None:
        project.results = op.odict()

        settings = project.settings
        settings.inj = 0            # Injection, don't change number
        settings.heterosexsex = [1, 2, 3]   # Homosexual sexual transmission, don't change number
        settings.homosexsex   = [4, 5, 6]     # Heterosexual sexual transmission, don't change number
        settings.mtct = 7           # MTCT
        settings.nmethods = 8       # 8 methods of transmission
        settings.nonmtctmethods = [settings.inj] + settings.heterosexsex + settings.homosexsex
        settings.regular    = [1, 4]
        settings.casual     = [2, 5]
        settings.commercial = [3, 6]
        settings.allmethodnames = ['Injection',
                               'Heterosexual sex (regular)','Heterosexual sex (casual)','Heterosexual sex (commercial)',
                               'Homosexual sex (regular)',  'Homosexual sex (casual)',  'Homosexual sex (commercial)',
                               'MTCT']
        settings.methodindsgroups = [[settings.inj], settings.heterosexsex, settings.homosexsex, [settings.mtct]]
        settings.methodnames = ['Injection', 'Heterosexual sex', 'Homosexual sex', 'MTCT']

        settings.now = 2023.0  # Default current year
        settings.dataend = 2040.0  # Default end year for data entry

def resetnumcircfromdata(project=None, **kwargs):
    '''
        Migration between revision 5 and 6,
        Resets fromdata attribute of numcirc to allow it to be updated from the databook in existing migrated projects
    '''
    if project is not None:
        for parset in project.parsets.values():
            parset.pars['numcirc'].fromdata = 1.0

def refreshlinks(project=None, **kwargs):
    '''
        Migration between revision 11 and 12
        Restores links, which resets odict_customs to have their correct function which could sometimes get linked to other resultsets
        or removed
        Removes _dcp, makes sure __deepcopy__ is linked to the current object and projectref linked to current projectref
        The causes of these mistakes has (hopefully been fixed)
    '''
    if project is not None:
        project.restorelinks()
        project.propagateversion(None, None, vals='all')
        project.results = op.odict()

        from types import MethodType

        # Now we clean up obj._dcp and obj.__deepcopy__ which under rare circumstances could be bound to another object
        def rebind_deepcopy_method(method, obj): # Create a new __deepcopy__ function that is sure to be bound to the correct object
            return type(method)(method.__func__, obj)

        seen = set()
        def clean_obj(obj, descend=False):
            if id(obj) in seen: return
            seen.add(id(obj))

            for key in ['scenparset', 'pars', 'programs']:
                try: clean_obj(getattr(obj, key))
                except: pass
                try: clean_obj(obj[key])
                except: pass

            if hasattr(obj, '_dcp'):
                del obj._dcp
            if hasattr(obj, '__deepcopy__') and isinstance(obj.__deepcopy__, MethodType):
                obj.__deepcopy__ = rebind_deepcopy_method(obj.__deepcopy__, obj)
            if hasattr(obj, 'projectref'):
                if obj.projectref is not None:
                    try:
                        linked_project = obj.projectref()
                        if id(linked_project) != id(project):
                            obj.projectref = op.dcp(obj.projectref)  # Removes the link, makes it a Link(LinkException)
                    except op.LinkException:
                        pass
            if hasattr(obj, 'func') and obj.func is not None and isinstance(obj.func, MethodType):
                clean_obj(obj.func.__self__)

        P = project
        for obj in [P, P.parsets, P.progsets] + P.parsets.values() + P.progsets.values() + P.scens.values() + P.results.values():
            clean_obj(obj)



##########################################################################################
### CORE MIGRATION FUNCTIONS
##########################################################################################
def versiontomigrateto(project, migrateversion='supported'):
    """
        migrateversion: 'supported' = up to the first supported version (default),
                    False = do not migrate at all (which prints a warning if the project version is not supported)
                    'minor' = migrate 2.a.b to 2.a.c with c as large as it can be within supported versions (minor calibration changes likely)
                    'major' = 'latest' = True = migrate 2.a.b to 2.x.y the latest version within supported versions (possible major calibration changes / databook changes)
                    or a specific version
    Returns:
        versiontomigrateto: either a version, False (don't migrate) or None which means couldn't find a version to migrate to
    """
    def versiontoint(version):  # only works up to 999,999 versions for each x.y.z
        split = version.split('.')
        return 1000000000000 * int(split[0]) + 1000000 * int(split[1]) + int(split[2])
    supported_versions = sorted(op.supported_versions, key=versiontoint)

    if not migrateversion: # Takes care of migrateversion = False
       return False

    if migrateversion == 'supported':
        # Need to migrate
        newversion = None
        for version in reversed(supported_versions):
            if op.compareversions(project.version, version) <= 0:
                newversion = version
        return newversion
    if migrateversion == 'minor':
        # Assuming x.y.z
        newversion = None
        version_split = project.version.split('.')
        for version in supported_versions: # find x.y.B that matches x.y.z
            new_version_split = version.split('.')
            if version_split[0] == new_version_split[0] and version_split[1] == new_version_split[1]:
                newversion = version
        return newversion
    if migrateversion == 'latest' or migrateversion == 'major' or migrateversion == True:
        return supported_versions[-1]

    # If it wasn't one of the above then migrateversion is a specific version
    import packaging
    if type(packaging.version.parse(migrateversion)) == packaging.version.Version: # check it is a valid version string
        requestversion_split = migrateversion.split('.')
        if len(requestversion_split) < 2: # '2' Warning: won't work with 3.x.y
            return supported_versions[-1] # latest
        if len(requestversion_split) == 2: # '2.12'
            newversion = None
            for version in supported_versions:  # find x.y.B that matches x.y.z
                version_split = version.split('.')
                if version_split[0] == requestversion_split[0] and version_split[1] == requestversion_split[1]:
                    newversion = version
            return newversion
        # '2.12.2' or some other exact version: note gets cut off after x.y.z
        return f'{requestversion_split[0]}.{requestversion_split[1]}.{requestversion_split[2]}'
    else:
        raise op.OptimaException(f'Could not parse migrateversion="{migrateversion}"')


def migrate(project, migrateversion='supported', verbose=2, die=None):
    """
    Migrate an Optima Project by inspecting the version and working its way up.
    migrateversion: 'supported' = up to the first supported version (default),
                    False = do not migrate at all (which prints a warning if the project version is not supported)
                    'minor' = migrate 2.a.b to 2.a.c with c as large as it can be within supported versions (minor calibration changes likely)
                    'major' = 'latest' = True = migrate 2.a.b to 2.x.y the latest version within supported versions (possible major calibration changes / databook changes)
                    or a specific version
    """
    if die is None: die = migrateversion !='supported' # supported is the default so don't die, but die otherwise

    migrations = setmigrations() # Get the migrations to run
    newversion = versiontomigrateto(project, migrateversion)

    if newversion is None:
        errormsg = f'WARNING: Could not find a version for project "{project.name}" to migrate to from version {project.version} using migrateversion={migrateversion}'
        if die: raise op.OptimaException(errormsg)
        else: print(errormsg)
        return project
    elif newversion == False:
        return project


    while str(project.version) != str(newversion):
        currentversion = str(project.version)

        # Check that the migration exists
        if not currentversion in migrations:
            if op.compareversions(currentversion, newversion)<0:
                errormsg = "WARNING, migrating %s failed: no migration exists from version %s to the desired version (%s)" % (project.name, currentversion, newversion)
            elif op.compareversions(currentversion, newversion)>0:
                errormsg = "WARNING, migrating %s failed: project version %s more recent than desired Optima version (%s)" % (project.name, currentversion, newversion)
            if die: raise op.OptimaException(errormsg)
            else:   op.printv(errormsg, 1, verbose)
            return project # Abort, if haven't died already

        # Do the migration
        nextversion,currentdate,migrator,msg = migrations[currentversion] # Get the details of the current migration -- version, date, function ("migrator"), and message
        op.printv('Migrating "%s" from %6s -> %s' % (project.name, currentversion, nextversion), 2, verbose)
        if migrator is not None: # Sometimes there is no upgrader
            try:
                migrator(project, verbose=verbose, die=die)
            except Exception as E:
                errormsg = 'WARNING, migrating "%s" from %6s -> %6s failed:\n%s' % (project.name, currentversion, nextversion, repr(E))
                if not hasattr(project, 'failedmigrations'): project.failedmigrations = [] # Create if it doesn't already exist
                project.failedmigrations.append(errormsg)
                if die: raise op.OptimaException(errormsg)
                else:   op.printv(errormsg, 1, verbose)
                return project # Abort, if haven't died already

        # Update project info
        project.version = nextversion # Update the version info

    # Restore links just in case
    project.restorelinks()

    # If any warnings were generated during the migration, print them now
    warnings = project.getwarnings()
    if warnings and die:
        errormsg = 'WARNING, Please resolve warnings in projects before continuing'
        if die: raise op.OptimaException(errormsg)
        else:   op.printv(errormsg+'\n'+warnings, 1, verbose)

    op.printv('Migration successful!', 3, verbose)
    return project

def migraterevisionfunc(project, migraterevision=True, verbose=2, die=False):
    revmigrations = setrevisionmigrations()  # Get the migrations to run
    if not hasattr(project, 'revision'): project.revision = '0'  ## TODO-kelvin int or string? - --- is this the place for this? Really would need a proper migration but we would need a revision for that

    if not migraterevision: # If we don't want to migrate
        return project

    if migraterevision == True or migraterevision == 'latest':
        newrevision = op.revision
    else: # A specific revision
        newrevision = migraterevision

    while str(project.revision) != str(newrevision):
        currentrevision = str(project.revision)

        # Check that the migration exists
        if not currentrevision in revmigrations:
            if op.compareversions(currentrevision, newrevision)<0: # We aren't yet where we want
                errormsg = "WARNING, migrating %s to revision %s failed: no migration exists from revision %s" % (project.name, newrevision, currentrevision)
            elif op.compareversions(currentrevision, newrevision)>0: # We are further where we want
                errormsg = "WARNING, migrating %s failed: project revision %s more recent than desired revision %s, current Optima revision (%s)" % (project.name, currentrevision, newrevision, op.revision)
            if die: raise op.OptimaException(errormsg)
            else:   op.printv(errormsg, 1, verbose)
            return project # Abort, if haven't died already

        # Do the migration
        nextrevision,currentdate,migrator,msg = revmigrations[currentrevision] # Get the details of the current migration -- newrevision, date, function ("migrator"), and message
        op.printv('Migrating revision "%s" from %6s -> %s' % (project.name, currentrevision, nextrevision), 2, verbose)
        if migrator is not None: # Sometimes there is no upgrader
            try:
                migrator(project, verbose=verbose, die=die)
            except Exception as E:
                errormsg = 'WARNING, migrating revision "%s" from %6s -> %6s failed:\n%s' % (project.name, currentrevision, nextrevision, repr(E))
                if not hasattr(project, 'failedmigrations'): project.failedmigrations = [] # Create if it doesn't already exist
                project.failedmigrations.append(errormsg)
                if die: raise op.OptimaException(errormsg)
                else:   op.printv(errormsg, 1, verbose)
                return project # Abort, if haven't died already

        # Update project info
        project.revision = nextrevision # Update the revision info

    # Restore links just in case
    project.restorelinks()

    # If any warnings were generated during the migration, print them now
    warnings = project.getwarnings()
    if warnings and die:
        errormsg = 'WARNING, Please resolve warnings in projects before continuing'
        if die: raise op.OptimaException(errormsg)
        else:   op.printv(errormsg+'\n'+warnings, 1, verbose)

    op.printv('Migration successful!', 3, verbose)
    return project

def loadproj(filename=None, folder=None, verbose=2, die=None, fromdb=False, migrateversion='supported', migraterevision='latest', updatefilename=True):
    ''' Load a saved project file -- wrapper for loadobj using legacy classes
        migrateversion: 'supported' = up to the first supported version (default),
                        False = do not migrate at all (which prints a warning if the project version is not supported)
                        'minor' = migrate 2.a.b to 2.a.c with c as large as it can be within supported versions (minor calibration changes likely)
                        'major' = 'latest' = migrate 2.a.b to 2.x.y the latest version within supported versions (possible major calibration changes / databook changes)
        migraterevision='latest'=True, False, or a specific revision (only latest is supported)
    '''
    if fromdb:    origP = op.loadstr(filename) # Load from database
    else:         origP = op.loadobj(filename=filename, folder=folder, verbose=(True if verbose>2 else None if verbose>0 else False), die=die) # Normal usage case: load from file


    if migrateversion:
        try:
            P = migrate(origP, migrateversion=migrateversion, verbose=verbose, die=die)
        except Exception as E:
            if die: raise E
            else:
                P = origP # Fail: return unmigrated version
                print(f'WARNING: Error when trying to update project "{P.name}" from version {P.version}:\n'+str(E))
    else: P = origP # Don't migrate

    if P.version not in op.supported_versions:
        errmsg = f'P.version={P.version} of this project "{P.name}" is not supported: {op.supported_versions} and you have set migrateversion={migrateversion}. '
        if die: raise OptimaException(errmsg)
        else: print('WARNING!: ' + errmsg + f'\n\tThis will likely cause problems until it is updated to one of the supported versions: {op.supported_versions}')

    try: # Note we don't have a `if migraterevsion` check, since we need to call migraterevisionfunc which adds P.revision if it needs it
        P = migraterevisionfunc(origP, migraterevision=migraterevision, verbose=verbose, die=die)
    except Exception as E:
        if die: raise E
        else: print(f'WARNING: Error when trying to update project "{P.name}" to revision {op.revision} from revision {P.revision}:\n'+str(E))

    if str(P.revision) != str(op.revision):
        errmsg = f'P.revision={P.revision} of this project "{P.name}" is not supported (only {op.revision}) and you have set migraterevision={migraterevision}. '
        if die: raise OptimaException(errmsg)
        else: print('WARNING!: ' + errmsg + f'\n\tThis will likely cause problems until it is updated to the latest revision {op.revision}')

    if not fromdb and updatefilename: P.filename = filename  # Update filename if not being loaded from a database - note this used to be in the `if migrateversion` block, not sure why?

    return P





##########################################################################################
### PORTFOLIO MIGRATIONS
##########################################################################################


def removegaoptim(portfolio):
    ''' First and perhaps only portfolio migration -- remove GAOptims class '''
    if hasattr(portfolio, 'gaoptims') and len(portfolio.gaoptims): # If it has GAOptims, "migrate" these to the new structure
        if len(portfolio.gaoptims)>1:
            print('WARNING, this portfolio has %i GAOptims but only the last one will be migrated! If you need the others, then use F = loadobj(<filename>) and save what you need manually.')
        portfolio.objectives = portfolio.gaoptims[-1].objectives
        portfolio.results = portfolio.gaoptims[-1].resultpairs # TODO: robustify
    for attr in ['gaoptims', 'outputstring']:
        try: delattr(portfolio, attr)
        except: pass
    portfolio.version = '2.3.5'
    return portfolio


def migrateportfolio(portfolio=None, verbose=2, die=True):
    
    # Rather than use the dict mapping, use a (series) of if statements
    if op.compareversions(portfolio.version, '2.3.5')<0:
        op.printv('Migrating portfolio "%s" from %6s -> %6s' % (portfolio.name, portfolio.version, '2.3.5'), 2, verbose)
        portfolio = removegaoptim(portfolio)
    
    if op.compareversions(portfolio.version, '2.9.0')<0:
        op.printv('Migrating portfolio "%s" from %6s -> %6s' % (portfolio.name, portfolio.version, '2.9.0'), 2, verbose)
        portfolio = addcascadeopt(portfolio=portfolio)
    
    # Update version number to the latest -- no other changes  should be necessary
    if op.compareversions(portfolio.version, '2.9.0')>=0:
        portfolio.version = op.supported_versions[-1]
    
    # Check to make sure it's the latest version -- should not happen, but just in case!
    if portfolio.version != op.supported_versions[-1]:
        errormsg = "No portfolio migration exists from version %s to the latest version (%s)" % (portfolio.version, op.supported_versions[-1])
        if die: raise op.OptimaException(errormsg)
        else:   op.printv(errormsg, 1, verbose)
    
    return portfolio


def loadportfolio(filename=None, folder=None, verbose=2):
    ''' Load a saved portfolio, migrating constituent projects -- NB, portfolio itself is not migrated (no need yet), only the projects '''

    op.printv('Loading portfolio %s...' % filename, 2, verbose)
    portfolio = op.loadobj(filename=filename, folder=folder, verbose=verbose) # Load portfolio
    portfolio = migrateportfolio(portfolio)
    
    for i in range(len(portfolio.projects)): # Migrate projects one by one
        op.printv('Loading project %s...' % portfolio.projects[i].name, 3, verbose)
        portfolio.projects[i] = migrate(portfolio.projects[i], verbose=verbose)
        portfolio.projects[i] = migraterevisionfunc(portfolio.projects[i], verbose=verbose)
    
    portfolio.filename = filename # Update filename
    
    return portfolio




    
    
    
