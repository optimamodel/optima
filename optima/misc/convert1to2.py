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

Version: 2016mar24
"""



##################################################################################################################
### Read old file
##################################################################################################################

from optima import Project, printv, odict, defaults, saveobj, dcp, OptimaException
from sys import argv
from numpy import nan, zeros
oldext = '.json'
newext = '.prj'
dosave = True




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




##################################################################################################################
### Convert data
##################################################################################################################

def convert1to2(infile=None, outfile=None):
    if infile is None: return # Stupid, I know...

    old = loaddata(infile)

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

    # Transitions (splits negative-valued births from aging matrix as well)
    new.data['birthtransit'] = zeros((nfemalepops,npops)).tolist()
    oldagematrix = dcp(old['data']['transit']['asym'])
    femalepops = new.data['pops']['female']
    femid = 0
    for x in xrange(len(oldagematrix)):
        for y in xrange(len(oldagematrix[0])):
            if oldagematrix[x][y] < 0:
                if femalepops[x]:
                    new.data['birthtransit'][femid][y] = -oldagematrix[x][y]
                    oldagematrix[x][y] = 0    
                else:
                    OptimaException('Error: A non-female is giving birth in the input data!')
        if femalepops[x]: femid += 1
    new.data['agetransit']   = oldagematrix
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
    ### Convert programs
    ##################################################################################################################
    from optima import Program, Programset
    from numpy import log
    print('Converting programs...')

    # Extract some useful variables
    ps = new.parsets[0].pars[0]
    nyears = len(old['data']['epiyears'])

    # Initialise storage variables
    newprogs = []
    targeteffects=[]

    # Create programs
    for progno, prog in enumerate(old['programs']):
        
        targetpars=[]
        targetpops=[]

        # Create program effects
        #import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        for effect in prog['effects']:
            if effect['param'][:6]=='condom': effect['param'] = 'cond'+effect['param'][6:]
            if effect['param']=='numfirstline': effect['param'] = 'numtx'
            
            # Extract effects
            if isinstance(effect['coparams'],list):
                ccopar = {'t':2016., 'intercept':(effect['coparams'][0],effect['coparams'][1]), prog['name']: (effect['coparams'][2],effect['coparams'][3])}
            else:            
                ccopar = {'t':2016., 'intercept':(0.,0.), prog['name']: []}

            # Convert partnership parameters 
            if ps[effect['param']].by=='pship':
                targetpships = list(set([pship for pship in ps[effect['param']].y.keys() if effect['popname'] in pship]))
                for targetpship in targetpships:
                    targetpars.append({'param':effect['param'], 'pop':targetpship})
                    targeteffects.append({'param':effect['param'], 'pop':targetpship, 'ccopar': ccopar})

            # Convert non-partnership parameters 
            else:
                targetpars.append({'param':effect['param'], 'pop':effect['popname']})
                targeteffects.append({'param':effect['param'], 'pop':effect['popname'], 'ccopar': ccopar})
        
        # Create program
        newprog = Program(short=prog['name'],
                          targetpars=targetpars,
                          targetpops=list(set([effect['popname'] for effect in prog['effects']]))
                          )

        # Get target population size
        targetpopsize = newprog.gettargetpopsize(t=2016, parset = new.parsets[0])

        # Add historical cost and coverage data
        for yearind in range(nyears):
            
    #        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
            if len(old['data']['costcov']['realcost'][progno])==1: # It's an assumption, apply to every year
                newcost = old['data']['costcov']['realcost'][progno][0]
            else:
                newcost = old['data']['costcov']['realcost'][progno][yearind]
            if len(old['data']['costcov']['cov'][progno])==1: # It's an assumption, apply to every year
                newcov = old['data']['costcov']['cov'][progno][0]
            else:
                newcov = old['data']['costcov']['cov'][progno][yearind]
            newprog.addcostcovdatum({'t': old['data']['epiyears'][yearind],
                                     'cost': newcost,
                                     'coverage': newcov})

        # Create cost functions
        sat = prog['ccparams']['saturation']
        cov_u = prog['ccparams']['coverageupper']
        cov_l = prog['ccparams']['coveragelower']
        cov = (cov_u+cov_l)/2
        fund = prog['ccparams']['funding']
        unitcost = -2*fund/(sat*targetpopsize*log((2*sat)/(sat+cov)-1))

        newprog.costcovfn.addccopar({'t': 2016.0, 
                                     'saturation':(sat, sat),
                                     'unitcost':(unitcost, unitcost)}) 


        # Append to list
        newprogs.append(newprog)

    # Create program set
    R = Programset(programs=newprogs)

    # Save old program effects to program set
    failures = 0
    for targeteffect in targeteffects:
         try: R.covout[targeteffect['param']][targeteffect['pop']].addccopar(targeteffect['ccopar'], overwrite=True)
         except:
             failures += 1
             print('Failure %i: conversion failed for \n%s\nvs\n%s' % (failures, R.covout[targeteffect['param']][targeteffect['pop']].ccopars, targeteffect['ccopar']))

    # Add program set to project
    new.addprogset(name='default', progset = R)

    # Compare outcoes under budget and calibration
    #comparison = new.progsets[0].compareoutcomes(parset=new.parsets[0], year=2016, doprint=True)







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

    # plotresults(new.parsets['v1-autofit'].getresults(), toplot=['prev-pops'])

    if outfile is None: outfile = infile[:-len(oldext)]+newext

    if dosave: saveobj(outfile, new)
    print('Done.')

    return new



try: 
    filename = argv[1]
    if filename.endswith(oldext): filename += oldext
    convert1to2(filename=filename)
except:
    pass