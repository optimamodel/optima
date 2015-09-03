# This file searchers for the Optima directory and adds it to the path
# Developers can add their paths here
# To use this file in other .py files in the tests folder, simply import it
# See runportfolio.py for example usage

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
sys.path.append(findoptima() + '/classes')