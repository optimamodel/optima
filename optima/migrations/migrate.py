import optima as op


def _TwoToTwoOneMigration(project):
    """
    Migration between Optima 2.0 and 2.1.
    """
    for scen in project.scens.values():
        if not hasattr(scen, 'uid'):
            scen.uid = op.uuid()

    project.version = "2.1"


_MIGRATIONS = {
    '2.0': _TwoToTwoOneMigration
}


def migrateproject(project):
    """
    Migrate an Optima Project by inspecting the version and working its way up.
    """
    while str(project.version) != str(op.__version__):
        if not str(project.version) in _MIGRATIONS:
            raise ValueError("We can't upgrade version %s" % (project.version,))

        upgrader = _MIGRATIONS[str(project.version)]

        print("Migrating from %s" % (project.version,))
        upgrader(project)
        print("Migrated to %s" % (project.version,))

    return project
