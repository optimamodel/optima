#!/usr/bin/env python2
'''
Convert a Python 2 Optima HIV project to Python 3. All that's required is removing
the datetime objects, which have screwy tzinfo.
'''

import sys
import six
import optima as op

if not six.PY2:
    raise Exception('This script must be run from Python2!')

def convertfile(filename, dosave=True):
    fileroot = filename[:-4]
    extension = filename[-4:]
    if extension == '.prj':
        P = op.loadproj(filename)
        obj = convertproj(P)
    elif extension == '.prt':
        F = op.loadportfolio(filename)
        obj = convertportfolio(F)
    else:
        raise Exception('Extension %s not recognized' % extension)
    newfilename = fileroot + '_py3' + extension
    obj.filename = newfilename
    if dosave:
        obj.save()
    return obj

def convertproj(P):
    P.created = str(P.created)
    P.modified = str(P.modified)
    P.spreadsheetdate = str(P.spreadsheetdate)
    P.data['meta']['date'] = str(P.data['meta']['date'])
    for structlist in [P.parsets, P.progsets, P.optims, P.results]:
        for item in structlist.values():
            try: item.created = str(item.created)
            except Exception as E: print('Could not convert created for %s (%s), moving on...' % (item, str(E)))
            if not isinstance(item, op.Resultset):
                try: item.modified = str(item.modified)
                except Exception as E: print('Could not convert modified for %s (%s), moving on...' % (item, str(E)))
    for result in P.results.values():
        for key in ['created', 'modified', 'spreadsheetdate']:
            result.projectinfo[key] = str(result.projectinfo[key])
            result.data['meta']['date'] = str(P.data['meta']['date'])
            if hasattr(result, 'optim'):
                result.optim.created = str(result.optim.created)
                result.optim.modified = str(result.optim.modified)
    return P

def convertportfolio(F):
    F.created = str(F.created)
    F.modified = str(F.modified)
    for key,P in F.projects.items():
        F.projects[key] = convertproj(P)
    for item in F.results.values():
        try: item.created = str(item.created)
        except Exception as E: print('Could not convert created %s (%s), moving on...' % (item, str(E)))
        try: item.modified = str(item.modified)
        except Exception as E: print('Could not convert modified %s (%s), moving on...' % (item, str(E)))
    return F

if __name__ == '__main__':
    if len(sys.argv)>1:
        filenames = sys.argv[1:]
        print('Converting files %s...' % filenames)
        for filename in filenames:
            try:
                obj = convertfile(filename)
            except Exception as E:
                print('Could not convert %s: %s' % (filename, str(E)))
