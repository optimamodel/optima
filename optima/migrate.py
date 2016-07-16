import optima as op


def _TwoToTwoOneMigration(project):

    for scen in project.scens.values():
        scen.uid = uuid()

    project.version = "2.1"


_MIGRATIONS = {
    '2.0': _TwoToTwoOneMigration
}

def migrateproject(project):
    """
    Migrate an Optima Project by inspecting the version and working its way up.
    """
    while project.version != __version__:
        if not project.version in _MIGRATIONS:
            raise ValueError("We can't upgrade version %s" % (project.__version__,))

        upgrader = _MIGRATIONS[project.version]
        upgrader(project)

    return project
