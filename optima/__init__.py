# -*- coding: utf-8 -*-
"""
Optima HIV -- HIV optimization and analysis tool
Copyright (C) 2016 by the Optima Consortium


This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.]
or
import optima as op
or
from optima import *

Note: do NOT modify this file directly; instead, modify optima.py -- this allows
Optima to be used from inside this directory, whereas otherwise everything would
have to be imported from the individual modules.


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


Version: 2016jan29
"""

# This means that if Optima is loaded as a module, it's expected to succeed
import __builtin__
__builtin__._failsilently = False

# Actually do all the imports
from optima import *
