# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.]
or
import optima as op
or
from optima import *

Version: 2015dec09
"""

## Load general modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp

## Load non-Optima-specific custom functions
from ballsd import *
from colortools import *
from utils import *

## Load Optima functions and classes
from settings import *
from loadspreadsheet import *
from makesimpars import *
from makespreadsheet import *
from parameters import *
from results import *
from model import *
from programs import *
from project import *
from makeplots import *
from gui import *