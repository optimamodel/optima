import optima as op



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
    Migration between Optima 2.0.2 and 2.0.3.
    """
    if hasattr(project, 'parsets'):
        for ps in project.parsets.values():
            if ps.pars[0].get('immediatecare'): del ps.pars[0]['immediatecare']
    if hasattr(project, 'data'):
        if project.data.get('immediatecare'): del project.data['immediatecare']
    project.version = "2.0.3"
    return None


def redotransitions(project, **kwargs):
    """
    Migration between Optima 2.0.3 and 2.0.4
    """
    from numpy import concatenate as cat
    from optima import Constant, loadtranstable

    # Update settings
    if hasattr(project, 'settings'):
        project.settings.healthstates = ['susreg', 'progcirc', 'undx', 'dx', 'care', 'usvl', 'svl', 'lost']
        project.settings.notonart = cat([project.settings.undx,project.settings.dx,project.settings.care,project.settings.lost])
        project.settings.alldx = cat([project.settings.dx,project.settings.care,project.settings.usvl,project.settings.svl,project.settings.lost])
        project.settings.allcare = cat([project.settings.care,project.settings.usvl,project.settings.svl])

        project.settings.allplhiv  = cat([project.settings.undx, project.settings.alldx])
        project.settings.allstates = cat([project.settings.sus, project.settings.allplhiv]) 
        project.settings.nstates   = len(project.settings.allstates) 
        project.settings.statelabels = project.settings.statelabels[:project.settings.nstates]
        project.settings.nhealth = len(project.settings.healthstates)

        if hasattr(project.settings, 'usecascade'): del project.settings.usecascade
        if hasattr(project.settings, 'tx'):         del project.settings.tx
        if hasattr(project.settings, 'off'):        del project.settings.off

    # Update variables in data
    if hasattr(project, 'data'):
        if project.data.get('immediatecare'):   del project.data['immediatecare']
        if project.data.get('biofailure'):      del project.data['biofailure']
        if project.data.get('restarttreat'):    del project.data['restarttreat']
        if project.data.get('stoprate'):        del project.data['stoprate']
        if project.data.get('treatvs'):         del project.data['treatvs']

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
        if project.data['const'].get('deathtreat'):     del project.data['const']['deathtreat']
        if project.data['const'].get('progusvl'):       del project.data['const']['progusvl']
        if project.data['const'].get('recovgt500'):     del project.data['const']['recovgt500']
        if project.data['const'].get('recovgt350'):     del project.data['const']['recovgt350']
        if project.data['const'].get('recovgt200'):     del project.data['const']['recovgt200']
        if project.data['const'].get('recovgt50'):      del project.data['const']['recovgt50']
        if project.data['const'].get('recovusvl'):      del project.data['const']['recovusvl']
        if project.data['const'].get('stoppropcare'):   del project.data['const']['stoppropcare']

    # Update parameters
    if hasattr(project, 'parsets'):
        for ps in project.parsets.values():
            for pd in ps.pars:
                
                # Remove old parameters
                if pd.get('biofailure'):        del pd['biofailure']
                if pd.get('deathtreat'):        del pd['deathtreat']
                if pd.get('immediatecare'):     del pd['immediatecare']
                if pd.get('progusvl'):          del pd['progusvl']
                if pd.get('recovgt500'):        del pd['recovgt500']
                if pd.get('recovgt350'):        del pd['recovgt350']
                if pd.get('recovgt200'):        del pd['recovgt200']
                if pd.get('recovgt50'):         del pd['recovgt50']
                if pd.get('recovusvl'):         del pd['recovusvl']
                if pd.get('restarttreat'):      del pd['restarttreat']
                if pd.get('stoppropcare'):      del pd['stoppropcare']
                if pd.get('stoprate'):          del pd['stoprate']

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

            # Rerun calibrations to update results appropriately
            project.runsim(ps.name)


    project.version = "2.0.4"
    return None




migrations = {
'2.0': versiontostr,
'2.0.0': addscenuid,
'2.0.1': addforcepopsize,
'2.0.2': delimmediatecare,
'2.0.3': redotransitions,
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
        try: 
            upgrader(project, verbose=verbose)
            op.printv("%s" % project.version, 2, verbose, indent=False)
        except Exception as E:
            print('Migration failed!!!!')
            raise E
    
    op.printv('Migration successful!', 1, verbose)

    return project
