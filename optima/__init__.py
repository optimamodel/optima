# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.]
or
import optima as op
or
from optima import *

This file has an unusual structure, since it builds up Optima as it goes along,
so within each module, you can use "from optima import <...>". In addition,
it imports the modules themselves starting with an underscore, then deletes the
original (so, e.g. optima.project is imported as optima._project, and optima.project
is deleted since it's confusing when "project" is used as an instance of a project).


Now, the legal part:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


Version: 2019jan09
"""


# Specify the version, for the purposes of figuring out which version was used to create a project
from .version import *

# Print the license
optimalicense = f'Optima HIV {"/".join(supported_versions)} ({revision}) {revisiondate} -- (c) Optima Consortium'
print(optimalicense)

# Create an empty list to stored failed imports
_failed = []


#####################################################################################################################
### Load helper functions/modules
#####################################################################################################################

# For Python 3 compatibility
import six
if six.PY3:
    basestring = str
    unicode = str

# General modules
from uuid import uuid4 as uuid
from copy import deepcopy as dcp

# Utilities -- import alphabetically
from .utils import *

#Utilities replaced by newer Sciris versions
from sciris import getdate
# For Optima version 2.11.4 we need sciris version 2.0.2 or later
from sciris import __version__ as sc_version, __versiondate__ as sc_versiondate
if compareversions(sc_version, '2.0.2') < 0:
    print(f'!! WARNING: you are using an old version of sciris: version {sc_version} from {sc_versiondate}.\nPlease update to the latest version using "pip install sciris --upgrade"')
    from multiprocessing import cpu_count
else:
    from sciris import cpu_count
del sc_version; del sc_versiondate

# Color definitions
from .colortools import *

# Optimization algorithm
from .asd import asd

# Interpolation
from .pchip import pchip, plotpchip


#####################################################################################################################
### Define debugging and exception functions/classes
#####################################################################################################################

# Optima Path
def optimapath(subdir=None, trailingsep=True):
    ''' Returns the parent path of the Optima module. If subdir is not None, include it in the path '''
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if subdir is not None:
        tojoin = [path, subdir]
        if trailingsep: tojoin.append('') # This ensures it ends with a separator
        path = os.path.join(*tojoin) # e.g. ['/home/optima', 'tests', '']
    return path

# Debugging information
def debuginfo(dooutput=False):
    output = '\nOptima debugging info:\n'
    output += '   Versions: %s\n' % supported_versions
    output += '   Revision: %s\n' % revision
    output += '   Branch:  %s\n' % gitinfo()[0]
    output += '   SHA:     %s\n' % gitinfo()[1][:7]
    output += '   Path:    %s\n' % optimapath()
    if dooutput:
        return output
    else:
        print(output)
        return None

class OptimaException(Exception):
    ''' A tiny class to allow for Optima-specific exceptions -- define this here to allow for Optima-specific info '''

    def __init__(self, errormsg, *args, **kwargs):
        if isinstance(errormsg, basestring): errormsg = errormsg+debuginfo(dooutput=True) # If it's not a string, not sure what it is, but don't bother with this
        Exception.__init__(self, errormsg, *args, **kwargs)


#####################################################################################################################
### Load Optima functions and classes
#####################################################################################################################

# File I/O
from sciris  import loadobj, saveobj, loadstr, dumpstr # Insist sciris is installed
from .fileio import * # CK: may want to tidy up

# Project settings
from .settings import *

# Generate results -- import first because parameters use results
from .results import Result, Resultset, Multiresultset, BOC, ICER, getresults

# Define the model parameters -- import before makespreadsheet because makespreadsheet uses partable to make a pre-filled spreadsheet
from .parameters import * # Parameter and Parameterset classes and methods

# Create a blank spreadsheet
try: from .makespreadsheet import *
except Exception as E: _failed.append('makespreadsheet: %s' % repr(E))

# Load a completed a spreadsheet
from .loadspreadsheet import *

# Define and run the model
from .model import *

# Define the programs and cost functions
from .programs import *

# Automatic calibration and sensitivity
from .calibration import *

# Scenario analyses
from .scenarios import *

# Optimization and ICER analyses
from .optimization import *

# Plotting functions
try: from .plotting import *
except Exception as E: _failed.append('plotting: %s' % repr(E))

#####################################################################################################################
### Load high-level modules that depend on everything else
#####################################################################################################################

# Load the code to load projects and portfolios (before defining them, oddly!)
from .loadtools import *
changelog = loadtools.setmigrations('changelog')

# Load batch functions (has to load projects, so has to come after migration)
from .batchtools import *

# Import the Project class that ties everything together
from .project import *

# Load the portfolio class (container of Projects), relies on batch functions, hence is here
from .portfolio import *

# Finally, load defaults
from .defaults import *


#####################################################################################################################
### Load optional Python GUI
#####################################################################################################################

# Load high level GUI module
try:
    from .gui import *
except Exception as E: _failed.append('gui: %s' % repr(E))

try:
    from .webserver import browser
except Exception as E: _failed.append('webserver: %s' % repr(E))


if len(_failed): print('The following non-critical import errors were encountered:\n%s' % _failed)
else: del _failed # If it's empty, don't bother keeping it
