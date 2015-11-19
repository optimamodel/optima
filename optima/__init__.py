# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 13:35:18 2015

@author: cliffk
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