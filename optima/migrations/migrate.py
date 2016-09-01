import optima as op
from numpy import nan


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
    for ps in project.parsets.values():
        for i in range(len(ps.pars)):
            ps.pars[i]['proppmtct'] = op.dcp(project.pars()['proptx'])
            ps.pars[i]['proppmtct'].name = 'Pregnant women and mothers on PMTCT'
            ps.pars[i]['proppmtct'].short = 'proppmtct'
    project.data['proppmtct'] = [[nan]*len(project.data['years'])]
    project.version = "2.0.4"
    return None


migrations = {
'2.0': versiontostr,
'2.0.0': addscenuid,
'2.0.1': addforcepopsize,
'2.0.2': delimmediatecare,
'2.0.3': addproppmtct,
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
