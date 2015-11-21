# -*- coding: utf-8 -*-
"""
ODICT

An ordered dictionary, like the OrderedDict class, but supporting list methods like integer referencing,
slicing, and appending.

Version: 2015nov21 by cliffk
"""


from collections import OrderedDict


class odict(OrderedDict):
    def __getitem__(self, key):
        ''' Allows getitem to support strings, integers, slices, lists, or arrays '''
        if type(key)==str: # Treat like a normal dict
            return dict.__getitem__(self,key)
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
            try:
                self.__getitem__(key.tolist()) # Try converting to a list
            except:
                raise Exception('Could not understand data type: not a str, int, slice, list, or array!')
    
    def __setitem__(self, key, value):
        ''' Allows setitem to support strings, integers, slices, lists, or arrays '''
        if type(key)==str:
            dict.__setitem__(self, key, value)
        elif type(key) in [int, float]: # Convert automatically from float...dangerous?
            thiskey = self.keys()[int(key)]
            dict.__setitem__(self, thiskey, value)
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
            try:
                self.__setitem__(key.tolist(), value) # Try converting to a list
            except:
                raise Exception('Could not understand data type: not a str, int, slice, list, or array!')
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
    
    def setkey(self, item, key):