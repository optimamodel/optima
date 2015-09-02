def findoptima():
    """ Find the directory that Optima exists in. """
    from os.path import exists
    optimadirs = [ # List all common directories here.
        '/u/cliffk/unsw/optima/server/src/sim',
        '/Users/robynstuart/Documents/Optima2/server/src/sim',
        'C:/Users/Ireporter/Documents/GitHub/Optima/server/src/sim',
        'D:/Work Projects/Optima/Optima/server/src/sim',
        '/Users/romesha/Desktop/Work/Optima/Optima/server/src/sim',
        'C:/Users/romesh/Desktop/optima/Optima/server/src/sim',
    ]
    for optimadir in optimadirs:
        if exists(optimadir):
            return optimadir
    raise Exception('Unfortunately the Optima directory cannot be found! Please add its path to the optimadirs list.')

import sys; 
sys.path.append(findoptima())
sys.path.append(findoptima() + '/legacy')



from sim import Sim
from simbudget import SimBudget
from simbudget2 import SimBudget2

from simbox import SimBox
from simboxopt import SimBoxOpt
from simboxcal import SimBoxCal

from portfolio import Portfolio
from programset import ProgramSet
from region import Region

from plot import plot