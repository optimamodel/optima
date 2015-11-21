# -*- coding: utf-8 -*-
"""
ODICT

An ordered dictionary, like the OrderedDict class, but supporting list methods like integer referencing,
slicing, and appending.

Version: 2015nov21 by cliffk
"""


from collections import OrderedDict
from _abcoll import *


class odict(OrderedDict):
    def __getitem__(self, key):
        ''' Allows getitem to support strings, integers, slices, lists, or arrays '''
        if type(key)==str: # Treat like a normal dict
            return OrderedDict.__getitem__(self,key)
        elif type(key) in [int, float]: # Convert automatically from float...dangerous?
            return self.values()[int(key)]
        elif type(key)==slice: # Handle a slice -- complicated
            if type(key.start) is int: startind = key.start
            elif type(key.start) is str: startind = self.keyind(key.start)
            elif key.start is None: startind = 0
            else: raise Exception('To use a slice, start must be either int or str (%s)' % key.start)
            if type(key.stop) is int: stopind = key.stop
            elif type(key.stop) is str: stopind = self.keyind(key.stop)
            elif key.stop is None: stopind = len(self)-1
            else: raise Exception('To use a slice, stop must be either int or str (%s)' % key.stop)
            if stopind<startind: raise Exception('Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind))
            return [self.__getitem__(i) for i in range(startind,stopind+1)] # +1 since otherwise confusing with names
        elif type(key)==list: # Iterate over items
            return [self.__getitem__(item) for item in key]
        else: # Try to convert to a list if it's an array or something
            return OrderedDict.__getitem__(self, key)

        
        
    def __setitem__(self, key, value):
        ''' Allows setitem to support strings, integers, slices, lists, or arrays '''
        if type(key)==str:
            OrderedDict.__setitem__(self, key, value)
        elif type(key) in [int, float]: # Convert automatically from float...dangerous?
            thiskey = self.keys()[int(key)]
            OrderedDict.__setitem__(self, thiskey, value)
        elif type(key)==slice:
            if type(key.start) is int: startind = key.start
            elif type(key.start) is str: startind = self.keyind(key.start)
            elif key.start is None: startind = 0
            else: raise Exception('To use a slice, start must be either int or str (%s)' % key.start)
            if type(key.stop) is int: stopind = key.stop
            elif type(key.stop) is str: stopind = self.keyind(key.stop)
            elif key.stop is None: stopind = len(self)-1
            else: raise Exception('To use a slice, stop must be either int or str (%s)' % key.stop)
            if stopind<startind: raise Exception('Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind))
            for valind,keyind in enumerate(range(startind,stopind+1)): # +1 since otherwise confusing with names
                self.__setitem__(self, keyind, value[valind])
        elif type(key)==list:
            for valind,thiskey in enumerate(key): # +1 since otherwise confusing with names
                self.__setitem__(self, thiskey, value[valind])
        else:
            OrderedDict.__setitem__(self, key, value)
        return None
    
    def __repr__(self):
        ''' Print a meaningful representation of the odict '''
        return '\n'.join(["#%i: '%s': %s" % (i, self.keys()[i], self.values()[i]) for i in range(len(self))])
    
    def keyind(self, item):
        ''' Return the index of a given key '''
        return self.keys().index(item)
    
    def valind(self, item):
        ''' Return the index of a given value '''
        return self.items().index(item)
    
    def append(self, item):
        ''' Support an append method, like a list '''
        keyname = str(len(self)) # Define the key just to be the current index
        self.__setitem__(keyname, item)
        return None
    
    def setkey(self, oldkey, newkey):
        ''' Change a key '''
        if type(oldkey) in [int, float]: keyind = oldkey
        elif type(oldkey) is str: keyind = self.keys().index(oldkey)
        else: raise Exception('Key type not recognized: must be int or str')
        self.keys()[keyind] = newkey
        return None