# how to run it locally:
# curl -XPOST -i http://localhost:5000/api/project/data/migrate?secret=40a0233e6b155cd08d8f8f4cd3ea85d854af454b334e80f896afff61

migrations = {
    0:'001_inhomogenities',
    1:'002_removebloat',
    2:'003_add_programs',
    3:'004_fix_ccparams'
}

def run_migrations(model):
    import importlib
    from sim.makeproject import current_version
    result = None #if nothing has to be changed
    # try to get project version from G (where it should be) or from top-level key (where it was)
    new_style_version = False
    G = model.get('G')
    if not G: return result # broken project, don't bother
    try:
        # assume we have version stored under G
        previous_version = model['G']['version']
        new_style_version = (previous_version is not None)
        print "new_style_version", new_style_version, previous_version
    except:
        # try to get version stored as a top-level key (old way)
        previous_version = model.get('version', 0)

    if not new_style_version: # nothing to change
        if 'version' in model: del model['version']
        model['G']['version'] = current_version
        result = model # we want to resave new model because version is saved differently
    if previous_version < current_version:
        for version in xrange(previous_version, current_version):
            print("%s - %s" % (version, version+1))
            current_module = importlib.import_module('versioning.'+ migrations[version], 'versioning')
            model = current_module.migrate(model)
            model['G']['version'] = version +1
        result = model # we want to resave new model because there were migrations
    return result
