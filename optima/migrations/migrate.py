import optima as op

def addscenuid(project, **kwargs):
    """
    Migration between Optima 2.0 and 2.1.
    """
    for scen in project.scens.values():
        if not hasattr(scen, 'uid'):
            scen.uid = op.uuid()
    project.version = "2.0.1"
    return None


def addforcepopsize(project, **kwargs):
    """
    Migration between Optima 2.0 and 2.1.
    """
    if not hasattr(project.settings, 'forcepopsize'):
        project.settings.forcepopsize = True
    project.version = "2.0.2"
    return None




migrations = {
    '2.0.0': addscenuid,
    '2.0.1': addforcepopsize,
}



def runmigrations(project, verbose=2):
    """
    Migrate an Optima Project by inspecting the version and working its way up.
    """
    while str(project.version) != str(op.__version__):
        if not str(project.version) in migrations:
            raise ValueError("We can't upgrade version %s" % (project.version,))

        upgrader = migrations[str(project.version)]

        op.printv("Migrating from %s" % project.version, 2, verbose)
        try: 
            upgrader(project, verbose=verbose)
            op.printv("Migrated to %s" % project.version, 2, verbose)
        except Exception as E:
            print('Migration failed!!!!')
            raise E

    return project
