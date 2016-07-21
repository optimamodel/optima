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


migrations = {
'2.0': versiontostr,
'2.0.0': addscenuid,
'2.0.1': addforcepopsize,
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
