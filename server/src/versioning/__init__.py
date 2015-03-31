current_version = 1

migrations = {
    0:'001_add_programs'
}

def run_migrations(model):
    import importlib
    previous_version = model.get('version', 0)
    if previous_version == current_version: return None
    for version in xrange(previous_version, current_version):
        print("%s - %s" % (version, version+1))
        current_module = importlib.import_module('versioning.'+ migrations[version], 'versioning')
        model = current_module.migrate(model)
        model['version'] = version +1
    return model