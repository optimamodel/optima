# how to run it locally:
# curl -XPOST -i http://localhost:5000/api/project/data/migrate?secret=40a0233e6b155cd08d8f8f4cd3ea85d854af454b334e80f896afff61

current_version = 2

migrations = {
    0:'001_inhomogenities',
<<<<<<< HEAD
    1:'002_removebloat'
=======
    1:'002_add_programs'
>>>>>>> removing-all-hardcoding-copy
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
