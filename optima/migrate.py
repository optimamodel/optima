import optima as op
from numpy import nan, concatenate as cat, array, arange


def addparameter(project=None, copyfrom=None, short=None, **kwargs):
    ''' 
    Function for adding a new parameter to a project -- used by several migrations.
    Use kwargs to arbitrarily specify the new parameter's properties.
    '''
    for ps in project.parsets.values():
        for i in range(len(ps.pars)):
            ps.pars[i][short] = op.dcp(project.pars()[copyfrom])
            ps.pars[i][short].short = short
            for kwargkey,kwargval in kwargs.items():
                setattr(ps.pars[i][short], kwargkey, kwargval)
    project.data[short] = [[nan]*len(project.data['years'])]


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
    for ps in project.parsets.values():
        for i in range(len(ps.pars)):
            ps.pars[i].pop('immediatecare', None)
    project.data.pop('immediatecare', None)
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
    project.settings.transnorm = 0.6 # Warning: should NOT match default since should reflect previous versions, which were hard-coded as 1.2 (this being the inverse of that)

    if hasattr(project.settings, 'usecascade'): del project.settings.usecascade
    if hasattr(project.settings, 'tx'):         del project.settings.tx
    if hasattr(project.settings, 'off'):        del project.settings.off

    # Update variables in data
    project.data.pop('immediatecare', None)
    project.data.pop('biofailure', None)
    project.data.pop('restarttreat', None)
    project.data.pop('stoprate', None)
    project.data.pop('treatvs', None)

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
    
    project.settings = op.Settings() # Completely refresh
    
    # Replace with original settings
    for settingkey,settingval in oldsettings.items(): 
        setattr(project.settings, settingkey, settingval) 
    
    project.version = "2.1.8"
    return None


<<<<<<< HEAD
def addcosttx(project, **kwargs):
    """
    Migration between Optima 2.1.8 and 2.1.9.
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
    kwargs['t'] = op.odict([('tot',array([2010.]))])
    kwargs['y'] = op.odict([('tot',array([100.]))]) # Setting to a non-trivial placeholder value
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)

    short = 'fixpropdx'
    copyfrom = 'deathacute'
    kwargs['name'] = 'Year to fix PLHIV aware of their status'
    kwargs['dataname'] = 'Year to fix PLHIV aware of their status'
    kwargs['datashort'] = 'fixpropdx'
    kwargs['y'] = nan
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

    short = 'fixpropsupp'
    copyfrom = 'fixpropdx'
    kwargs['name'] = 'Year to fix people on ART with viral suppression'
    kwargs['dataname'] = 'Year to fix people on ART with viral suppression'
    kwargs['datashort'] = 'fixpropsupp'
    addparameter(project=project, copyfrom=copyfrom, short=short, **kwargs)


    project.version = "2.1.9"
    return None
#Unit cost of treatment	Unit cost of treatment	costtx	costtx	(0, 'maxpopsize')	tot	timepar	no	no	0	None	0	None	1
=======
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
>>>>>>> develop





def redoprograms(project, **kwargs):
    """
    Migration between Optima 2.1.9 and 2.2 -- convert CCO objects from simple dictionaries to parameters.
    """
    project.version = "2.2"
    print('NOT IMPLEMENTED')
    return None




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
<<<<<<< HEAD
'2.1.8': addcosttx,
#'2.1.8': redoprograms,
=======
'2.1.8': addoptimscaling,
#'2.2': redoprograms,
>>>>>>> develop
}





def migrate(project, verbose=2):
    """
    Migrate an Optima Project by inspecting the version and working its way up.
    """
    while str(project.version) != str(op.__version__):
        if not str(project.version) in migrations:
            raise op.OptimaException("We can't upgrade version %s to latest version (%s)" % (project.version, op.__version__))

        upgrader = migrations[str(project.version)]

        op.printv("Migrating from %s ->" % project.version, 2, verbose, newline=False)
        upgrader(project, verbose=verbose) # Actually easier to debug if don't catch exception
        op.printv("%s" % project.version, 2, verbose, indent=False)
    
    op.printv('Migration successful!', 3, verbose)

    return project









def loadproj(filename, verbose=2):
    ''' Load a saved project file -- wrapper for loadobj using legacy classes '''
    
    # Create legacy classes for compatibility -- FOR FUTURE
#    class CCOF(): pass
#    class Costcov(): pass
#    class Covout(): pass
#    op.programs.CCOF = CCOF
#    op.programs.Costcov = Costcov
#    op.programs.Covout = Covout

    proj = migrate(op.loadobj(filename, verbose=verbose), verbose=verbose)
    
#    del op.programs.CCOF
#    del op.programs.Costcov
#    del op.programs.Covout
    
    return proj