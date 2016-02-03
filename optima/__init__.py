# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from .optima import Project, Parameters [etc.] [preferred]
or
import optima as op
or
from .optima import *

The __init__.py file imports all functions and classes defined in this file..

Since other functions import optima.py and optima.py imports other functions, 
weird race conditions can happen. Thus, it's designed to silently fail once
it gets up to the latest module that it can successfully import. To make it
fail loudly, do a find-and-replace for "pass #" with blank to re-enable the
print statements.

I'm sorry this file is so ugly. Believe me, it hurts me more than it hurts you.



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


Version: 2016jan30 by cliffk
"""

optimalicense = '''
Optima HIV -- HIV optimization and analysis tool
Copyright (C) 2016 by the Optima Consortium
'''
print(optimalicense)




## Specify the version, for the purposes of figuring out which version was used to create a project
__version__ = 2.0 



## Load general modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp


from . import asd as _asd
from .asd import asd



from . import pchip as _pchip
from .pchip import pchip, plotpchip



from . import colortools # Load high-level module as well
from .colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor



from . import utils # Load high-level module as well
from .utils import blank, checkmem, dataindex, defaultrepr, findinds, getdate, gitinfo, loadobj, loads, objectid, objatt, objmeth, objrepr, odict, OptimaException, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, saveobj, saves, scaleratio, setdate, sigfig, smoothinterp, tic, toc # odict class



## Load Optima functions and classes

from . import settings as _settings # Inter-project definitions, e.g. health states
from .settings import Settings, convertlimits, gettvecdt



from . import makespreadsheet as _makespreadsheet
from .makespreadsheet import makespreadsheet, makeeconspreadsheet, default_datastart, default_dataend # For making a blank spreadsheet



from . import loadspreadsheet as _loadspreadsheet
from .loadspreadsheet import loadspreadsheet # For loading a filled out spreadsheet



from . import results as _results
from .results import Result, Resultset, Multiresultset, BOC, getresults  # Result and Results classes -- odd that it comes before parameters, but parameters need getresults()



from . import parameters as _parameters # Load high-level module as well
from .parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars, partable, loadpartable, getresults, applylimits # Parameter and Parameterset classes



from . import model as _model
from .model import model, runmodel # The thing that actually runs the model



from . import programs as _programs # High-level module
from .programs import Program, Programset, vec2budget # Define programs



from . import economics as _economics
from .economics import loadeconomics, loadeconomicsspreadsheet, makeecontimeseries, getartcosts # Misc economic modules



from . import calibration as _calibration
from .calibration import sensitivity, autofit # Calibration functions



from . import scenarios as _scenarios # Load high-level module as well -- WARNING, somewhat like to be overwritten by user
from .scenarios import Parscen, Budgetscen, Coveragescen, runscenarios, makescenarios, defaultscenarios, getparvalues # Scenario functions



from . import optimization as _optimization
from .optimization import Optim, minoutcomes, minmoney, defaultobjectives # Scenario functions



from . import plotting as _plotting # Load high-level module as well
from .plotting import getplotselections, makeplots # Create the plots



## Want to add more modules to Optima? Do that here (unless they're non-essential plotting functions)



## Load optional plotting functions -- instead of failing, just redefine as an error message so still "available"


try: from . import gui # All Python GUI functions
except: gui = None # If fails, try individual functions as well


try: from .gui import plotresults
except: 
    def plotresults(*args, **kwargs): print('Note: plotresults() could not be imported, but everything else should work')


try: from .gui import pygui # Handle the Python plotting
except:
    def pygui(*args, **kwargs): print('Note: pygui() could not be imported, but everything else should work')


try: from .gui import browser # Handle the browser-based plotting
except:
    def browser(*args, **kwargs): print('Note: browser() could not be imported, but everything else should work')


try: from .gui import manualfit # Do manual fitting
except:
    def manualfit(*args, **kwargs): print('Note: manualfit() could not be imported, but everything else should work')


try: from .gui import plotpeople # Plot all people
except:
    def plotpeople(*args, **kwargs): print('Note: plotpeople() could not be imported, but everything else should work')


try: from .gui import plotpars # Plot all people
except:
    def plotpars(*args, **kwargs): print('Note: plotpars() could not be imported, but everything else should work')




## Import the Project class that ties everything together
import project as _project
from .project import Project # Project class



import portfolio as _portfolio
from .portfolio import Portfolio # Portfolio class (container of Projects)


try:
    import geospatial as _geospatial
    from .geospatial import geogui # Import GUI tools for geospatial analysis
except: 
    def geogui(*args, **kwargs): print('Note: geogui() could not be imported, but everything else should work')



# Finally, load defaults
import defaults