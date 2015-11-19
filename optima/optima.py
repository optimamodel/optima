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

## Top-level imports
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp

## Load general modules
from numpy import array # TEMP?

## Load classes
from project import *
from settings import *
from parameters import *

## Load other Optima functions
from ballsd import *
from colortools import *
from loadspreadsheet import *
from model import *
from utils import *
