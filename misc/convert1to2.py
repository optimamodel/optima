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

Version: 2016mar03
"""



##################################################################################################################
### Read old spreadsheet
##################################################################################################################

from optima import Project, printv, odict, defaults, saveobj, dcp, plotresults
from sys import argv
from numpy import nan, zeros
defaultfilename = 'Sudan_20160216.json'#'example.json'
oldext = '.json'
newext = '.prj'
dosave = True

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


## Convert the things that do not convert themselves
npops = len(new.data['pops']['short']) # Number of population groups
new.data['npops'] = npops
new.data['pops']['age'] = [[15,49] for _ in range(npops)] # Assume 15-49 for all population groups
nmalepops = sum(new.data['pops']['male'])
nfemalepops = sum(new.data['pops']['female'])
def missingtot(value=0): return [[value]] # If missing, replace with a value indicating an assumption
def missingpop(value=0, npops=npops): return [[value] for _ in range(npops)] # If missing, replace with a value indicating an assumption


## Now, handle everything else

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
new.data['birth']    = [old['data']['txrx']['birth'][0] for _ in range(nfemalepops)] # Duplicate nfpops times
new.data['treatvs']  = missingtot(0.8) # WARNING, is this appropriate?

# Optional
new.data['optnumtest']   = old['data']['opt']['numtest']
new.data['optnumdiag']   = old['data']['opt']['numdiag']
new.data['optnuminfect'] = missingtot(nan)
new.data['optprev']      = old['data']['opt']['prev']
new.data['optplhiv']     = missingtot(nan)
new.data['optdeath']     = old['data']['opt']['death']
new.data['optnewtreat']  = old['data']['opt']['newtreat']
new.data['propdx']        = missingtot(nan)
new.data['propcare']      = missingtot(nan)
new.data['proptx']        = missingtot(nan) 
new.data['propsupp']      = missingtot(nan)

# Cascade 
new.data['immediatecare'] = missingpop(nan)
new.data['linktocare']    = missingpop(nan)
new.data['stoprate']      = missingpop(nan)
new.data['leavecare']     = missingpop(nan)
new.data['biofailure']    = missingtot(nan)
new.data['freqvlmon']     = missingtot(nan)
new.data['restarttreat']  = missingtot(nan)

# Sex
new.data['numactsreg'] = old['data']['sex']['numactsreg']
new.data['numactscas'] = old['data']['sex']['numactscas']
new.data['numactscom'] = old['data']['sex']['numactscom']
new.data['condomreg']  = old['data']['sex']['condomreg']
new.data['condomcas']  = old['data']['sex']['condomcas']
new.data['condomcom']  = old['data']['sex']['condomcom']
new.data['propcirc']   = old['data']['sex']['circum']
new.data['numcirc']    = missingpop(nan, npops=nmalepops)

# Injecting
new.data['numactsinj'] = old['data']['inj']['numinject']
new.data['sharing']    = old['data']['inj']['sharing']
new.data['numost']     = old['data']['inj']['numost']

# Partnerships
new.data['pships'] = odict()
for which in ['reg', 'cas', 'com', 'inj']:
    new.data['part'+which] = old['data']['pships'][which]
    new.data['pships'][which] = []
    for row in range(new.data['npops']):
        for col in range(new.data['npops']):
            if new.data['part'+which][row][col]: new.data['pships'][which].append((new.data['pops']['short'][row],new.data['pops']['short'][col]))

# Transitions
new.data['birthtransit'] = zeros((nfemalepops,npops)).tolist()
new.data['agetransit']   = old['data']['transit']['asym']
new.data['risktransit']  = old['data']['transit']['sym']

# Constants
new.data['const'] = defaultproject.data['const'] 


##################################################################################################################
### Run simulation and copy calibration parameters
##################################################################################################################

print('Running simulation and calibration...')

# Create parameter set
new.makeparset()

# Copy over fitted aspects of the calibration
new.parsets[0].pars[0]['initprev'].y[:] = old['F'][0]['init'][:]
new.parsets[0].pars[0]['force'].y[:]    = old['F'][0]['force'][:]
new.parsets[0].pars[0]['inhomo'].y[:]   = old['F'][0]['inhomo'][:]

## Run simulation
#new.runsim()

##################################################################################################################
### Autocalibrate to match old calibration curves
##################################################################################################################

# First work out the indices for the calibration results that would map onto data years.

tvec = old['M']['tvec']
epiyears = old['data']['epiyears']
invdt = int(round(1/(tvec[1]-tvec[0])))
endind = int(round((epiyears[-1]-epiyears[0])*invdt)) + 1

new.runsim()
new.data['hivprev'] = [[[y[x] if z==0 else nan for x in xrange(0,endind,invdt)] for y in old['R']['prev']['pops'][0]] for z in xrange(3)]
new.autofit(name='v1-autofit', orig='default', fitwhat=['force'], maxtime=None, maxiters=1000, inds=None) # Run automatic fitting

new.data['hivprev'] = old['data']['key']['hivprev']
new.runsim('v1-autofit')   # Re-simulate autofit curves, but for old data.
#alt.manualfit(orig='v1-autofit')

##################################################################################################################
### Plotting
##################################################################################################################

#print('Doing calibration...')
#new.manualfit()

plotresults(new.parsets['v1-autofit'].getresults(), toplot=['prev-pops'])

if dosave: saveobj(filename.strip(oldext)+newext, new)
print('Done.')



