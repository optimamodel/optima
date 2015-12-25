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

# analysis:ignore

## Load general modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp

## Load non-Optima-specific custom functions
from ballsd import ballsd
from colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor
from utils import blank, checkmem, dataindex, findinds, getdate, load, loads, objectid, odict, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, save, saves, setdate, sigfig, smoothinterp, tic, toc # odict class

## Load Optima functions and classes
from settings import Settings
from makespreadsheet import makespreadsheet, default_datastart, default_dataend
from loadspreadsheet import loadspreadsheet
from parameters import Timepar, Popsizepar, Parameterset # Parameter and Parameterset classes
from results import Result, Resultset # Result and Results classes
from model import model
from programs import Program, Programset
from project import Project, version # Project class
from makeplots import epiplot
from gui import gui