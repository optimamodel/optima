"""
CONVERT1TO2

Script for converting a 1.0 project to a 2.0 project.

Usage:
    python convert1to2.py <oldproject>
    e.g.
    python convert1to2.py malawi.json

Copies the data over, copies some aspects of the calibration over.

TODO: copy programs
TODO: copy scenario settings
TODO: copy optimization settings

Version: 2016mar02
"""



##################################################################################################################
### Read old spreadsheet
##################################################################################################################

from optima import Project, printv, odict, defaults
from sys import argv
defaultfilename = 'example.json'
oldext = '.json'
newext = '.prj'

print('Loading data...')



def loaddata(filename, verbose=0):
    """
    Loads the file and imports json data from it -- copied from dataio.py in Optima 1.0
    """
    import json
    printv('Loading data...', 1, verbose)
    rfid = open(filename,'rb')
    data = fromjson(json.load(rfid))
    rfid.close()
    printv('...done loading data.', 2, verbose)
    return data


def fromjson(x):
    """ Convert an object from JSON-serializable format, handling e.g. Numpy arrays -- copied from dataio.py in Optima 1.0 """
    NP_ARRAY_KEYS = set(["np_array", "np_dtype"])
    from numpy import asarray, dtype, nan

    if isinstance(x, dict):
        dk = x.keys()
        if len(dk) == 2 and set(dk) == NP_ARRAY_KEYS:
            return asarray(fromjson(x['np_array']), dtype(x['np_dtype']))
        else:
            return dict( (k, fromjson(v)) for k,v in x.iteritems() )
    elif isinstance(x, (list, tuple)):
        return type(x)( fromjson(v) for v in x )
    elif x is None:
        return nan
    else:
        return x

try: filename = argv[1]
except: filename = defaultfilename
if not filename.endswith(oldext): filename += oldext

old = loaddata(filename)


##################################################################################################################
### Convert data
##################################################################################################################

print('Converting data...')

## Initialization
defaultproject = defaults.defaultproject('simple', verbose=0) # Used for filling in constants and some missing values
new = Project() # Create blank project
new.data = odict() # Initialize data object
new.data['years'] = old['data']['epiyears'] # Copy years

## Population metadata
new.data['pops'] = odict()
new.data['pops']['short']     = old['data']['meta']['pops']['short']
new.data['pops']['long']      = old['data']['meta']['pops']['long']
new.data['pops']['male']      = old['data']['meta']['pops']['male']
new.data['pops']['female']    = old['data']['meta']['pops']['female']
new.data['pops']['injects']   = old['data']['meta']['pops']['injects']
new.data['pops']['sexworker'] = old['data']['meta']['pops']['sexworker']
new.data['npops'] = len(new.data['pops']['short']) # Number of population groups
new.data['pops']['age']       = [[15,49] for _ in range(new.data['npops'])] # Assume 15-49 for all population groups


missing = None
toconvert = None

# Key variables
new.data['popsize'] = old['data']['key']['popsize']
new.data['hivprev'] = old['data']['key']['hivprev']

# Epi variables
new.data['death']   = old['data']['epi']['death']
new.data['stiprev'] = old['data']['epi']['stiprevulc']
new.data['tbprev']  = old['data']['epi']['tbprev']

# Test & treat
new.data['hivtest']  = old['data']['txrx']['hivtest']
new.data['aidstest'] = old['data']['txrx']['aidstest']
new.data['numtx']    = old['data']['txrx']['numfirstline']
new.data['prep']     = old['data']['txrx']['prep']
new.data['numpmtct'] = old['data']['txrx']['numpmtct']
new.data['breast']   = old['data']['txrx']['breast']
new.data['birth']    = toconvert
new.data['treatvs']  = missing

# Optional
new.data['optnumtest']   = old['data']['opt']['numtest']
new.data['optnumdiag']   = old['data']['opt']['numdiag']
new.data['optnuminfect'] = missing
new.data['optprev']      = old['data']['opt']['prev']
new.data['optplhiv']     = missing
new.data['optdeath']     = old['data']['opt']['death']
new.data['optnewtreat']  = old['data']['opt']['newtreat']

# Cascade
new.data['propdx']        = missing
new.data['propcare']      = missing 
new.data['proptx']        = missing 
new.data['propsupp']      = missing 
new.data['immediatecare'] = missing 
new.data['linktocare']    = missing 
new.data['stoprate']      = missing 
new.data['leavecare']     = missing 
new.data['biofailure']    = missing 
new.data['freqvlmon']     = missing 
new.data['restarttreat']  = missing 

# Sex
new.data['numactsreg'] = old['data']['sex']['numactsreg']
new.data['numactscas'] = old['data']['sex']['numactscas']
new.data['numactscom'] = old['data']['sex']['numactscom']
new.data['condomreg']  = old['data']['sex']['condomreg']
new.data['condomcas']  = old['data']['sex']['condomcas']
new.data['condomcom']  = old['data']['sex']['condomcom']
new.data['propcirc']   = old['data']['sex']['circum']
new.data['numcirc']    = missing

# Injecting
new.data['numactsinj'] = old['data']['inj']['numinject']
new.data['sharing']    = old['data']['inj']['sharing']
new.data['numost']     = old['data']['inj']['numost']

# Partnerships
new.data['numcirc'] 
'partreg', 'partcas', 'partcom', 'partinj', 'pships',

# Transitions
new.data['birthtransit'] = missing
new.data['agetransit']   = missing
new.data['risktransit']  = old['data']['transit']['sym']

# Constants
new.data['const'] = defaultproject.data['const'] 


##################################################################################################################
### Convert calibration
##################################################################################################################




print('Done.')



