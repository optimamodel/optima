# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.]
or
import optima as op
or
from optima import *


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


Version: 2016nov03 by cliffk
"""






## Specify the version, for the purposes of figuring out which version was used to create a project
from .version import version

# Print the license
optimalicense = 'Optima HIV %s -- (c) 2017 by the Optima Consortium' % version
print(optimalicense)

# Create an empty list to stored failed imports
_failed = [] 


#####################################################################################################################
### Load helper functions/modules
#####################################################################################################################

## General modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp

## Utilities
from . import utils # Load high-level module as well
from .utils import blank, checkmem, checktype, compareversions, dataindex, dataframe, defaultrepr, findinds, findnearest, getdate, getvaliddata, gitinfo, indent, isnumber, isiterable, Link, LinkException, loadbalancer, objectid, objatt, objmeth, objrepr, odict, pd, perturb, printarr, printdata, printv, promotetoarray, promotetolist, quantile, runcommand, sanitize, scaleratio, sigfig, slacknotification, smoothinterp, tic, toc, vec2obj

## Optimization algorithm
from . import asd as _asd
from .asd import asd

## Interpolation
from . import pchip as _pchip
from .pchip import pchip, plotpchip

## Color definitions
from . import colortools # Load high-level module as well
from .colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor


#####################################################################################################################
### Define debugging and exception functions/classes
#####################################################################################################################

## Optima Path
def optimapath(subdir=None, trailingsep=True):
    ''' Returns the parent path of the Optima module. If subdir is not None, include it in the path '''
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if subdir is not None:
        tojoin = [path, subdir]
        if trailingsep: tojoin.append('') # This ensures it ends with a separator
        path = os.path.join(*tojoin) # e.g. ['/home/optima', 'tests', '']
    return path

## Debugging information
def debuginfo(dooutput=False):
    output = '\nOptima debugging info:\n'
    output += '   Version: %s\n' % version
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

## Data I/O
from . import dataio
from .dataio import loadobj, saveobj, loadstr, dumpstr, loadpartable, loadtranstable, loaddatapars # CK: may want to tidy up

## Project settings
from . import settings as _settings # Inter-project definitions, e.g. health states
from .settings import Settings, convertlimits, gettvecdt

## Generate results -- import first because parameters use results
from . import results as _results
from .results import Result, Resultset, Multiresultset, BOC, getresults

## Define the model parameters -- import before makespreadsheet because makespreadsheet uses partable to make a pre-filled spreadsheet
from . import parameters as _parameters
from .parameters import Par, Dist, Constant, Metapar, Timepar, Popsizepar, Yearpar, Parameterset, makepars, makesimpars, applylimits, comparepars, comparesimpars # Parameter and Parameterset classes

## Create a blank spreadsheet
try:
    from . import makespreadsheet as _makespreadsheet
    from .makespreadsheet import makespreadsheet, makeprogramspreadsheet, default_datastart, default_dataend
except Exception as E: _failed.append('makespreadsheet: %s' % E.__repr__())

## Load a completed a spreadsheet
from . import loadspreadsheet as _loadspreadsheet
from .loadspreadsheet import loadspreadsheet, loadprogramspreadsheet

## Define and run the model
from . import model as _model
from .model import model, runmodel

## Define the programs and cost functions
from . import programs as _programs
from .programs import Program, Programset

## Automatic calibration and sensitivity
from . import calibration as _calibration
from .calibration import autofit 

## Scenario analyses
from . import scenarios as _scenarios 
from .scenarios import Parscen, Budgetscen, Coveragescen, Progscen, runscenarios, makescenarios, baselinescenario, setparscenvalues, defaultscenarios

## Optimization analyses
from . import optimization as _optimization
from .optimization import Optim, defaultobjectives, defaultconstraints, optimize, outcomecalc

## Plotting functions
from . import plotting as _plotting 
from .plotting import getplotselections, makeplots, plotepi, plotcascade, plotallocations, plotcostcov


#####################################################################################################################
### Want to add more modules to Optima? Do that above this line (unless they're non-essential plotting functions)
#####################################################################################################################



#####################################################################################################################
### Load optional plotting functions
#####################################################################################################################

## Load high level GUI module
try: 
    from . import gui
    from .gui import plotresults, pygui, plotpeople, plotpars, browser, manualfit
except Exception as E: _failed.append('gui: %s' % E.__repr__())


#####################################################################################################################
### Finally, load high-level modules that depend on everything else
#####################################################################################################################

## Import the Project class that ties everything together
import project as _project
from .project import Project

# Finally, load defaults
from . import defaults
from .defaults import defaultproject, defaultprogset, defaultprograms, demo

# And really finally, load other random things that don't matter
import migrate as _migrate
from .migrate import migrate, loadproj, loadportfolio, optimaversion

# Really really finally, load the portfolio class (container of Projects), relies on loadproj, hence is here
import portfolio as _portfolio
from .portfolio import Portfolio 

# And really really finally, load geospatial functions (has to load projects, so has to come after migration)
try:
    from . import batchtools
    from .batchtools import batchautofit, batchBOC
except Exception as E: _failed.append('batchtools: %s' % E.__repr__())

try:
    import geospatial as _geospatial
    from .geospatial import geogui # Import GUI tools for geospatial analysis
except Exception as E: _failed.append('geospatial: %s' % E.__repr__())

if len(_failed): print('The following import errors were encountered:\n%s' % _failed)
else: del _failed # If it's empty, don't bother keeping it
