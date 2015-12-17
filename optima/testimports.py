# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.]
or
import optima as op
or
from optima import *

Version: 2015dec17
"""

_namespace = {}
_newimports = {}
_clashes = {}
_namespace['_default'] = set(globals().keys())


_packages = [
'ballsd', 
'colortools', 
'utils',
'settings',
'loadspreadsheet',
'makesimpars',
'makespreadsheet',
'parameters',
'results',
'model',
'programs',
'project',
'makeplots',
'gui',
]

## Load general modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp
_namespace['_general'] = set(globals().keys())
_newimports['_general'] = set(globals().keys()) - _namespace['_default']
_clashes['_general'] = set([])

for _package in _packages:
    _imported = __import__(_package, globals(), locals(), ['*'])
    for k in dir(_imported): globals()[k] = getattr(_imported, k)
    _newimports[_package] = set(dir(_imported))
    _namespace[_package] = set(globals().keys())
    _clashes[_package] = _newimports[_package] & _namespace[_package]

fucked = set([item for sublist in _clashes.values() for item in sublist])