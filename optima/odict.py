# -*- coding: utf-8 -*-
"""
ODICT

An ordered dictionary, like the OrderedDict class, but supporting list methods like integer referencing,
slicing, and appending.

Version: 2015nov21 by cliffk
"""


from _abcoll import *


class odict(dict):
    'Dictionary that remembers insertion order and can be used like a list'
    # An inherited dict maps keys to values.
    # The inherited dict provides __getitem__, __len__, __contains__, and get.
    # The remaining methods are order-aware.
    # Big-O running times for all methods are the same as regular dictionaries.

    # The internal self.__map dict maps keys to links in a doubly linked list.
    # The circular doubly linked list starts and ends with a sentinel element.
    # The sentinel element never gets deleted (this simplifies the algorithm).
    # Each link is stored as a list of length three:  [PREV, NEXT, KEY].

    def __init__(self, *args, **kwds):
        '''Initialize an ordered dictionary.  The signature is the same as
        regular dictionaries, but keyword arguments are not recommended because
        their insertion order is arbitrary.

        '''
        print('init')
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__root
        except AttributeError:
            self.__root = root = []                     # sentinel node
            root[:] = [root, root, None]
            self.__map = {}
        self.__update(*args, **kwds)

    def __setitem__(self, key, value, PREV=0, NEXT=1, dict_setitem=dict.__setitem__):
        print('setitem')
        'od.__setitem__(i, y) <==> od[i]=y'
        # Setting a new item creates a new link at the end of the linked list,
        # and the inherited dictionary is updated with the new key/value pair.
        if key not in self:
            root = self.__root
            last = root[PREV]
            last[NEXT] = root[PREV] = self.__map[key] = [last, root, key]
        dict_setitem(self, key, value)

    
    #############################################################################################################
    ## CK's modifications
    #############################################################################################################
    def __getitem__(self, key):
        ''' Allows getitem to support strings, integers, slices, lists, or arrays '''
        print('getitem')
        if type(key)==str:
            return dict.__getitem__(self,key)
        elif type(key)==int:
            return self.values()[key]
        elif type(key)==slice:
            out = []
            print('hi!!!')
            print(slice.start)
            print(slice.stop)
            print('biii!!!')
            if type(key.start) is int: startind = key.start
            elif type(key.start) is str: startind = self.keyind(key.start)
            elif key.start is None: startind = 0
            else: raise Exception('To use a slice, start must be either int or str (%s)' % key.start)
            if type(key.stop) is int: stopind = key.stop
            elif type(key.stop) is str: stopind = self.keyind(key.stop)
            elif key.stop is None: stopind = len(self.keys())-1
            else: raise Exception('To use a slice, stop must be either int or str (%s)' % key.stop)
            if stopind<startind: raise Exception('Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind))
            for i in range(startind,stopind+1): # +1 since otherwise confusing with names
                out.append(self.values()[i])
            return out
        elif type(key)==list:
            return [self.__getitem__(item) for item in key]
        else:
            try:
                self.__getitem__(key.tolist()) # Try converting to a list
            except:
                raise Exception('Could not understand data type: not a str, int, slice, list, or array!')
    
    def keyind(self, item):
        ''' Return the index of a given key '''
        return self.keys().index(item)
    
    def valind(self, item):
        ''' Return the index of a given value '''
        return self.items().index(item)
    
  




    #############################################################################################################
    ## CK's modifications
    #############################################################################################################


  
    def __delitem__(self, key, PREV=0, NEXT=1, dict_delitem=dict.__delitem__):
        print('delitem')
        'od.__delitem__(y) <==> del od[y]'
        # Deleting an existing item uses self.__map to find the link which gets
        # removed by updating the links in the predecessor and successor nodes.
        dict_delitem(self, key)
        link_prev, link_next, key = self.__map.pop(key)
        link_prev[NEXT] = link_next
        link_next[PREV] = link_prev

    def __iter__(self):
        print('iter')
        'od.__iter__() <==> iter(od)'
        # Traverse the linked list in order.
        NEXT, KEY = 1, 2
        root = self.__root
        curr = root[NEXT]
        while curr is not root:
            yield curr[KEY]
            curr = curr[NEXT]

    def __reversed__(self):
        print('reversed')
        'od.__reversed__() <==> reversed(od)'
        # Traverse the linked list in reverse order.
        PREV, KEY = 0, 2
        root = self.__root
        curr = root[PREV]
        while curr is not root:
            yield curr[KEY]
            curr = curr[PREV]

    def clear(self):
        print('clear')
        'od.clear() -> None.  Remove all items from od.'
        for node in self.__map.itervalues():
            del node[:]
        root = self.__root
        root[:] = [root, root, None]
        self.__map.clear()
        dict.clear(self)

    # -- the following methods do not depend on the internal structure --

    def keys(self):
        print('keys')
        'od.keys() -> list of keys in od'
        return list(self)

    def values(self):
        print('values')
        'od.values() -> list of values in od'
        return [self[key] for key in self]

    def items(self):
        print('items')
        'od.items() -> list of (key, value) pairs in od'
        return [(key, self[key]) for key in self]

    def iterkeys(self):
        print('iterkeys')
        'od.iterkeys() -> an iterator over the keys in od'
        return iter(self)

    def itervalues(self):
        print('itervalues')
        'od.itervalues -> an iterator over the values in od'
        for k in self:
            yield self[k]

    def iteritems(self):
        print('iteritems')
        'od.iteritems -> an iterator over the (key, value) pairs in od'
        for k in self:
            yield (k, self[k])

    update = MutableMapping.update

    __update = update # let subclasses override update without breaking __init__

    __marker = object()

    def pop(self, key, default=__marker):
        print('pop')
        '''od.pop(k[,d]) -> v, remove specified key and return the corresponding
        value.  If key is not found, d is returned if given, otherwise KeyError
        is raised.

        '''
        if key in self:
            result = self[key]
            del self[key]
            return result
        if default is self.__marker:
            raise KeyError(key)
        return default

    def setdefault(self, key, default=None):
        print('setdefault')
        'od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od'
        if key in self:
            return self[key]
        self[key] = default
        return default

    def popitem(self, last=True):
        print('popitem')
        '''od.popitem() -> (k, v), return and remove a (key, value) pair.
        Pairs are returned in LIFO order if last is true or FIFO order if false.

        '''
        if not self:
            raise KeyError('dictionary is empty')
        key = next(reversed(self) if last else iter(self))
        value = self.pop(key)
        return key, value

    def __repr__(self, _repr_running={}):
        print('repr')
        'od.__repr__() <==> repr(od)'
        call_key = id(self), _get_ident()
        if call_key in _repr_running:
            return '...'
        _repr_running[call_key] = 1
        try:
            if not self:
                return '%s()' % (self.__class__.__name__,)
            return '%s(%r)' % (self.__class__.__name__, self.items())
        finally:
            del _repr_running[call_key]

    def __reduce__(self):
        print('reduce')
        'Return state information for pickling'
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        for k in vars(odict()):
            inst_dict.pop(k, None)
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def copy(self):
        print('copy')
        'od.copy() -> a shallow copy of od'
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        print('fromkeys')
        '''OD.fromkeys(S[, v]) -> New ordered dictionary with keys from S.
        If not specified, the value defaults to None.

        '''
        self = cls()
        for key in iterable:
            self[key] = value
        return self

    def __eq__(self, other):
        print('eq')
        '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
        while comparison to a regular mapping is order-insensitive.

        '''
        if isinstance(other, odict):
            return len(self)==len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        print('ne')
        'od.__ne__(y) <==> od!=y'
        return not self == other

    # -- the following methods support python 3.x style dictionary views --

    def viewkeys(self):
        print('viewkeys')
        "od.viewkeys() -> a set-like object providing a view on od's keys"
        return KeysView(self)

    def viewvalues(self):
        print('viewvalues')
        "od.viewvalues() -> an object providing a view on od's values"
        return ValuesView(self)

    def viewitems(self):
        print('viewitems')
        "od.viewitems() -> a set-like object providing a view on od's items"
        return ItemsView(self)