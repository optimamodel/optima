import optima as op
from numpy import nan, concatenate as cat


def migrate(project, verbose=2):
    """
    Migrate an Optima Project by inspecting the version and working its way up.
    """
    return project


class TwoPointZero(object):
    to_version = "2.0.0"

    def when_done(self, project):
        pass


class TwoZeroZero(object):
    to_version = "2.0.1"

    def when_done(self, project):
        for scen in project.scens.values():
            if not hasattr(scen, 'uid'):
                scen.uid = op.uuid()


class TwoZeroOne(object):
    to_version = "2.0.2"

    def when_done(self, project):
        if not hasattr(project.settings, 'forcepopsize'):
            project.settings.forcepopsize = True


class TwoZeroTwo(object):
    to_version = "2.0.3"

    def when_done(self, project):
        for ps in project.parsets.values():
            for i in range(len(ps.pars)):
                ps.pars[i].pop('immediatecare', None)
        project.data.pop('immediatecare', None)


class TwoZeroThree(object):
    to_version = "2.0.4"

    def when_done(self, project):

        for ps in project.parsets.values():
            for i in range(len(ps.pars)):
                ps.pars[i]['proppmtct'] = op.dcp(project.pars()['proptx'])
                ps.pars[i]['proppmtct'].name = 'Pregnant women and mothers on PMTCT'
                ps.pars[i]['proppmtct'].short = 'proppmtct'
        project.data['proppmtct'] = [[nan]*len(project.data['years'])]


class TwoZeroFour(object):
    to_version = "2.1"

    def when_done(self, project):

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


class TwoOne(object):
    to_version = "2.1.1"

    def when_done(self, project):

        keys = ['propdx', 'propcare', 'proptx', 'propsupp', 'proppmtct']
        for key in keys:
            fullkey = 'opt'+key
            if fullkey not in project.data.keys():
                if key in project.data.keys():
                    project.data[fullkey] = project.data.pop(key)
                else:
                    raise op.OptimaException('Key %s not found, but key %s not found either' % (fullkey, key))


class TwoOneOne(object):
    to_version = "2.1.2"

    def when_done(self, project):

        ps = project.settings
        ps.allevercare    = cat([ps.care, ps.usvl, ps.svl, ps.lost]) # All people EVER in care


object_migrations = {
    "2.0": TwoPointZero,
    "2.0.0": TwoZeroZero,
    "2.0.1": TwoZeroOne,
    "2.0.2": TwoZeroTwo,
    "2.0.3": TwoZeroThree,
    "2.0.4": TwoZeroFour,
    "2.1": TwoOne,
    "2.1.1": TwoOneOne
}


def migrate_obj(obj, state, verbose=2):

    obj_name = obj.__class__.__name__

    if not "_optimaversion" in state:

        if "version" in state:
            state["_optimaversion"] = state["version"]
        else:
            op.printv("This doesn't have an optima version in the object, so just letting it go")

    while str(state["_optimaversion"]) != str(op.__version__):

        migration = object_migrations[str(state["_optimaversion"])]()

        if hasattr(migration, obj_name):
            getattr(migration, obj_name)(state)

        # Update the version
        state["_optimaversion"] = migration.to_version

        obj.__dict__ = state

        if obj_name == "Project":
            if hasattr(migration, "when_done"):
                migration.when_done(obj)
            obj.version = migration.to_version

        state = obj.__dict__

    op.printv('Migration successful!', 1, verbose)

    return state
