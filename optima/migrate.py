import optima as op
from numpy import nan, isnan, concatenate as cat, array


def addparameter(project=None, copyfrom=None, short=None, **kwargs):
    ''' 
    Function for adding a new parameter to a project -- used by several migrations.
    Use kwargs to arbitrarily specify the new parameter's properties.
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
    project.data[short] = [[nan]*len(project.data['years'])]
    return None


def removeparameter(project=None, short=None, datashort=None, verbose=False, die=False):
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


def addwarning(project=None, message=None):
    ''' Add a warning to the project, which is printed when migrated or loaded '''
    if not hasattr(project, 'warnings') or type(project.warnings)!=str: # If no warnings attribute, create it
        project.warnings = ''
    project.warnings += '\n'*3+str(message) # # Add this warning
    return None


def versiontostr(project, **kwargs):
    """
    Convert Optima version number from number to string.
    """
    project.version = "2.0.0"
    return None
    

def addscenuid(project, **kwargs):
    """
    Migration between Optima 2.0.0 and 2.0.1.
    """
    for scen in project.scens.values():
        if not hasattr(scen, 'uid'):
            scen.uid = op.uuid()
    project.version = "2.0.1"
    return None


def addforcepopsize(project, **kwargs):
    """
    Migration between Optima 2.0.1 and 2.0.2.
    """
    if not hasattr(project.settings, 'forcepopsize'):
        project.settings.forcepopsize = True
    project.version = "2.0.2"
    return None


def delimmediatecare(project, **kwargs):
    """
    Migration between Optima 2.0.2 and 2.0.3 -- WARNING, will this work for scenarios etc.?
    """
    removeparameter(project, short='immediatecare', datashort='immediatecare')
    project.version = "2.0.3"
    return None


def addproppmtct(project, **kwargs):
    """
    Migration between Optima 2.0.3 and 2.0.4.
    """
    addparameter(project=project, copyfrom='proptx', short='proppmtct', name='Pregnant women and mothers on PMTCT')
    project.version = "2.0.4"
    return None


def redotransitions(project, dorun=False, **kwargs):
    """
    Migration between Optima 2.0.4 and 2.1
    """
    from numpy import concatenate as cat
    from optima import Constant, loadtranstable

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
                addwarning(project, msg)

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
            pd['deathsvl']          = Constant(0.23,    limits=(0,'maxmeta'),       by='tot', auto='const', fittable='const', name='Relative death rate on suppressive ART (unitless)',                 short='deathsvl')
            pd['deathusvl']         = Constant(0.4878,  limits=(0,'maxmeta'),       by='tot', auto='const', fittable='const', name='Relative death rate on unsuppressive ART (unitless)',               short='deathusvl')
            pd['svlrecovgt350']     = Constant(2.2,     limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Treatment recovery into CD4>500 (years)',                           short='svlrecovgt350')
            pd['svlrecovgt200']     = Constant(1.42,    limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Treatment recovery into CD4>350 (years)',                           short='svlrecovgt200')
            pd['svlrecovgt50']      = Constant(2.14,    limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Treatment recovery into CD4>200 (years)',                           short='svlrecovgt50')
            pd['svlrecovlt50']      = Constant(0.66,    limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Treatment recovery into CD4>50 (years)',                            short='svlrecovlt50')
            pd['treatfail']         = Constant(0.16,    limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Treatment failure rate',                                            short='treatfail')
            pd['treatvs']           = Constant(0.2,     limits=(0,'maxduration'),   by='tot', auto='const', fittable='const', name='Time after initiating ART to achieve viral suppression (years)',    short='treatvs')
            pd['usvlproggt500']     = Constant(0.026,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Progression from CD4>500 to CD4>350 on unsuppressive ART',          short='usvlproggt500')
            pd['usvlproggt350']     = Constant(0.1,     limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Progression from CD4>350 to CD4>200 on unsuppressive ART',          short='usvlproggt350')
            pd['usvlproggt200']     = Constant(0.162,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Progression from CD4>200 to CD4>50 on unsuppressive ART',           short='usvlproggt200')
            pd['usvlproggt50']      = Constant(0.09,    limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Progression from CD4>50 to CD4<50 on unsuppressive ART',            short='usvlproggt50')
            pd['usvlrecovgt350']    = Constant(0.15,    limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Recovery from CD4>350 to CD4>500 on unsuppressive ART',             short='usvlrecovgt350')
            pd['usvlrecovgt200']    = Constant(0.053,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Recovery from CD4>200 to CD4>350 on unsuppressive ART',             short='usvlrecovgt200')
            pd['usvlrecovgt50']     = Constant(0.117,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Recovery from CD4>50 to CD4>200 on unsuppressive ART',              short='usvlrecovgt50')
            pd['usvlrecovlt50']     = Constant(0.111,   limits=(0,'maxrate'),       by='tot', auto='const', fittable='const', name='Recovery from CD4<50 to CD4>50 on unsuppressive ART',               short='usvlrecovlt50')

            # Add transitions matrix
            pd['rawtransit'] = loadtranstable(npops = project.data['npops'])
            
            # Convert rates to durations
            for transitkey in ['agetransit','risktransit']:
                for p1 in range(pd[transitkey].shape[0]):
                    for p2 in range(pd[transitkey].shape[1]):
                        thistrans = pd[transitkey][p1,p2]
                        if thistrans>0: pd[transitkey][p1,p2] = 1./thistrans # Invert if nonzero
            
            # Convert more rates to transitions
            for key in ['progacute', 'proggt500', 'proggt350', 'proggt200', 'proggt50']:
                pd[key].y = 1./pd[key].y # Invert
            

        # Rerun calibrations to update results appropriately
        if dorun: project.runsim(ps.name)

    project.version = "2.1"
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
    project.version = "2.1.1"
    return None


def addalleverincare(project, **kwargs):
    """
    Migration between Optima 2.1.1 and 2.1.2.
    """
    ps = project.settings
    ps.allevercare    = cat([ps.care, ps.usvl, ps.svl, ps.lost]) # All people EVER in care
    project.version = "2.1.2"
    return None


def removenumcircdata(project, **kwargs):
    """
    Migration between Optima 2.1.2 and 2.1.3.
    """
    project.data.pop('numcirc',None)        
    project.version = "2.1.3"
    return None


def removepopcharacteristicsdata(project, **kwargs):
    """
    Migration between Optima 2.1.3 and 2.1.4.
    """
    project.data['pops'].pop('sexworker',None)        
    project.data['pops'].pop('injects',None)        
    project.version = "2.1.4"
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
    project.version = "2.1.5"
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

    project.version = "2.1.6"
    return None


def adddataend(project, **kwargs):
    """
    Migration between Optima 2.1.6 and 2.1.7.
    """
    if not hasattr(project.settings, 'dataend'):
        if hasattr(project, 'data'):
            project.settings.dataend = project.data['years'][-1]
        else: project.settings.dataend = project.settings.end

    project.version = "2.1.7"
    return None


def fixsettings(project, **kwargs):
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
    
    project.settings = op.Settings() # Completely refresh -- WARNING, will mean future migrations to settings aren't necessary!
    
    # Replace with original settings
    for settingkey,settingval in oldsettings.items(): 
        setattr(project.settings, settingkey, settingval) 
    
    project.version = "2.1.8"
    return None


def addoptimscaling(project, **kwargs):
    """
    Migration between Optima 2.1.8 and 2.1.9.
    """
    ## New attribute for new feature
    for optim in project.optims.values():
        if 'budgetscale' not in optim.objectives.keys():
            optim.objectives['budgetscale'] = [1.]

    project.version = "2.1.9"
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
    
    project.version = "2.1.10"
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
        newpars = op.makepars(data = tmpdata, verbose=verbose, die=die) # Remake parameters using data, forging boldly ahead come hell or high water
        
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
                    if all(newpars['treatvs'].prior.pars==op.Dist().pars): # See if defaults are used
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
    
    project.version = "2.2"
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
            addwarning(project, msg)
    
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
    kwargs['prior'] = {'dist':'uniform', 'pars':(requiredvldata[1], requiredvldata[2])}
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)

    project.version = "2.2.1"

    return None
        

def addprojectinfotoresults(project, verbose=2, **kwargs):
    ''' Add project info to resultsets so they can be loaded '''
    
    for item in project.parsets.values()+project.progsets.values()+project.optims.values()+project.results.values():
        item.projectref = op.Link(project)
        try:    del item.project
        except: op.printv('No project attribute found for %s' % item.name, 3, verbose)
            
    for result in project.results.values():
        result.projectinfo = project.getinfo()
    
    project.version = '2.2.2'
    
    return None


def redoparameterattributes(project, **kwargs):
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
    kwargs['prior'] = {'dist':'uniform', 'pars':project.settings.transnorm*array([ 0.9,  1.1])}
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)
    
    project.version = '2.3'
    
    return None


def removespreadsheet(project, **kwargs):
    ''' Remove the binary spreadsheet (it's big, and unnecessary now that you can write data) '''
    delattr(project, 'spreadsheet')
    project.version = '2.3.1'
    return None

#def redoprograms(project, **kwargs):
#    """
#    Migration between Optima 2.2.1 and 2.3 -- convert CCO objects from simple dictionaries to parameters.
#    """
#    project.version = "2.2"
#    print('NOT IMPLEMENTED')
#    return None




migrations = {
'2.0':   versiontostr,
'2.0.0': addscenuid,
'2.0.1': addforcepopsize,
'2.0.2': delimmediatecare,
'2.0.3': addproppmtct,
'2.0.4': redotransitions,
'2.1':   makepropsopt,
'2.1.1': addalleverincare,
'2.1.2': removenumcircdata,
'2.1.3': removepopcharacteristicsdata,
'2.1.4': addaidsleavecare,
'2.1.5': addaidslinktocare,
'2.1.6': adddataend,
'2.1.7': fixsettings,
'2.1.8': addoptimscaling,
'2.1.9': addpropsandcosttx,
'2.1.10':redoparameters,
'2.2':   redovlmon,
'2.2.1': addprojectinfotoresults,
'2.2.2': redoparameterattributes,
'2.3':   removespreadsheet,
#'2.2': redoprograms,
}





def migrate(project, verbose=2, die=False):
    """
    Migrate an Optima Project by inspecting the version and working its way up.
    """
    while str(project.version) != str(op.version):
        if not str(project.version) in migrations:
            raise op.OptimaException("We can't upgrade version %s to latest version (%s)" % (project.version, op.version))

        upgrader = migrations[str(project.version)]

        op.printv("Migrating from %s ->" % project.version, 2, verbose, newline=False)
        upgrader(project, verbose=verbose, die=die) # Actually easier to debug if don't catch exception
        op.printv("%s" % project.version, 2, verbose, indent=False)
    
    op.printv('Migration successful!', 3, verbose)
    
    # If any warnings were generated during the migration, print them now
    warnings = project.getwarnings()
    if warnings and die: 
        errormsg = 'Please resolve warnings in projects before continuing'
        raise op.OptimaException(errormsg)

    return project









def loadproj(filename=None, verbose=2, die=False):
    ''' Load a saved project file -- wrapper for loadobj using legacy classes '''
    
    # Create legacy classes for compatibility -- FOR FUTURE
#    class CCOF(): pass
#    class Costcov(): pass
#    class Covout(): pass
#    op.programs.CCOF = CCOF
#    op.programs.Costcov = Costcov
#    op.programs.Covout = Covout
    
    class Spreadsheet(object): pass
    op.project.Spreadsheet = Spreadsheet

    try:    origP = op.loadobj(filename, verbose=verbose) # Normal usage case: load from file
    except: origP = op.loads(filename) # Alternate usage case: load from some other source

    P = migrate(origP, verbose=verbose, die=die)
    
#    del op.programs.CCOF
#    del op.programs.Costcov
#    del op.programs.Covout
    
    return P





def loadportfolio(filename=None, verbose=2):
    ''' Load a saved portfolio, migrating constituent projects -- NB, portfolio itself is not migrated (no need yet), only the projects '''
    
    op.printv('Loading portfolio %s...' % filename, 2, verbose)
    F = op.loadobj(filename, verbose=verbose) # Load portfolio
    
    
    for i in range(len(F.projects)): # Migrate projects one by one
        op.printv('Loading project %s...' % F.projects[i].name, 3, verbose)
        F.projects[i] = migrate(F.projects[i], verbose=verbose)
    
    F.version = op.version # Update version number
    
    return F



def optimaversion(filename=None, version=None, branch=None, sha=None, verbose=False, die=False):
    '''
    Reads the current script file and adds Optima version info. Simply add the line
    
    optimaversion(__file__)
    
    to a script file, and on running it will automatically re-save it as e.g.
    
    optimaversion(__file__) # Version: 2.1.11 | Branch: optima-version-for-scripts | SHA: e2620b9e849e0bd1c9115891df112e6744a26469
    
    Note: you can also use e.g. op.optimaversion(__file__), as long as "optimaversion(__file__)" appears.
    
    If version, branch, or sha arguments are supplied, then it will raise an exception if they don't match, e.g.
    
    optimaversion(__file__, version='2.1.4')
    
    Version: 2017jan29
    '''
    
    # Preliminaries
    shalength = 6 # Don't use the whole thing, it's ugly and unnecessary
    if filename is None: # Check to make sure a file name is given
        errormsg = 'Please call this function like this: optimaversion(__file__)'
        if die: raise op.OptimaException(errormsg)
        else: print(errormsg); return None
    currversion = op.version # Get Optima version info
    currbranch,currsha = op.gitinfo(die=die) # Get git info, dying on failure if requested
    if version is not None and version!=currversion: # Optionally check that versions match
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
    versionstring = ' # Version: %s | Branch: %s | SHA: %s\n' % (currversion, currbranch, currsha[:shalength+1]) # Create string to write
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
        
    
    # Write script file
    try: 
        f = open(filename, 'w')
    except:
        errormsg = 'Could not open file "%s" for writing' % filename
        if die: raise op.OptimaException(errormsg)
        else: print(errormsg); return None
    if verbose: print('Writing file %s' % filename)
    try: 
        f.writelines(alllines) # Just write everything
    except: 
        errormsg = 'optimaversion() write failed on %s' % filename
        if die: raise op.OptimaException(errormsg)
        else: print(errormsg); return None
    f.close()
    
    return None
    
    
    