# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.]
or
import optima as op
or
from optima import *

NB: the GUI is not imported, since this requires PyQt4, which is both not likely to exist
and slow to import.

Version: 2015nov21
"""

## Load general modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp

## Load non-Optima-specific custom functions
from ballsd import *
from colortools import *
from utils import *
from odict import *

## Load Optima functions and classes
from settings import *
from loadspreadsheet import *
from makesimpars import *
from makespreadsheet import *
from parameters import *
from results import *
from model import *
from project import *