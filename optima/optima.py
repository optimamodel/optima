# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.]
or
import optima as op
or
from optima import *



Version: 2015nov19
"""

## Load general modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp

## Load non-Optima-specific functions
from ballsd import *
from colortools import *
from utils import *

## Load Optima classes
from project import *
from parameters import *
from settings import *
from results import *

## Load other Optima functions
from loadspreadsheet import *
from makesimpars import *
from makespreadsheet import *
from model import *

## Optional imports
try: from gui import *
except:pass