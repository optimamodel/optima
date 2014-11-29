"""
Four little functions to get and set data from nested dictionaries. The first two were stolen from:
    http://stackoverflow.com/questions/14692690/access-python-nested-dictionary-items-via-a-list-of-keys

"getnested" will get the value for the given list of keys:
    getnested(foo, ['a','b'])

"setnested" will set the value for the given list of keys:
    setnested(foo, ['a','b'], 3)

"makenested" will recursively generate a dictionary with the given list of keys:
    makenested(foo, ['a','b'])

"iternested" will return a list of all the twigs in the current dictionary:
    twigs = iternested(foo)

Example 1:
    from nested import makenested, getnested, setnested
    foo = {}
    makenested(foo, ['a','b'])
    foo['a']['b'] = 3
    print getnested(foo, ['a','b'])    # 3
    setnested(foo, ['a','b'], 7)
    print getnested(foo, ['a','b'])    # 7
    makenested(foo, ['yerevan','parcels'])
    setnested(foo, ['yerevan','parcels'], 'were tasty')
    print foo['yerevan']  # {'parcels': 'were tasty'}

Example 2:
    from nested import makenested, iternested, setnested
    foo = {}
    makenested(foo, ['a','x'])
    makenested(foo, ['a','y'])
    makenested(foo, ['a','z'])
    makenested(foo, ['b','a','x'])
    makenested(foo, ['b','a','y'])
    count = 0
    for twig in iternested(foo):
        count += 1
        setnested(foo, twig, count)   # {'a': {'y': 1, 'x': 2, 'z': 3}, 'b': {'a': {'y': 4, 'x': 5}}}

Version: 2014nov29 by cliffk
"""



def getnested(nesteddict, keylist): 
    """ Get a value from a nested dictionary"""
    output = reduce(lambda d, k: d[k], keylist, nesteddict)
    return output



def setnested(nesteddict, keylist, value): 
    """ Set a value in a nested dictionary """
    getnested(nesteddict, keylist[:-1])[keylist[-1]] = value
    return None # Modify nesteddict in place



def makenested(nesteddict, keylist):
    """ Make the nested keys listed in keylist into a nested dictionary """
    currentlevel = nesteddict
    for i,key in enumerate(keylist):
        try:
            currentlevel[key]
        except:
            if type(currentlevel) != dict: currentlevel = dict()
            if i==len(keylist)-1:
                currentlevel[key] = None
            else:
                currentlevel[key] = dict()
        currentlevel = currentlevel[key] # Recursion!! Ahahahaha!
    return None # Modify nesteddict in place



def iternested(nesteddict):
    """ Loop over all twigs of a nested dict -- spent a long time thining how to make this more elegant and couldn't :("""
    output = []
    
    def trykeys(mightbedict):
        """ Return a list of keys if a dict, otherwise return an empty list """
        if type(mightbedict)==dict: return mightbedict.keys()
        else: return []
    
    for k1 in trykeys(nesteddict):
        dict1 = nesteddict[k1]
        l2=False
        for k2 in trykeys(dict1):
            dict2 = dict1[k2]
            l2=True
            l3=False
            for k3 in trykeys(dict2):
                dict3 = dict2[k3]
                l3=True
                l4=False
                for k4 in trykeys(dict3):
                    dict4 = dict3[k4]
                    l4=True
                    l5=False
                    for k5 in trykeys(dict4):
                        l5 = True
                        output.append([k1, k2, k3, k4, k5])
                        print('WARNING, reached maximum level of nested dictionary recursion (5), sorry this code sucks so much')
                    if not(l5): output.append([k1, k2, k3, k4])
                if not(l4): output.append([k1, k2, k3])
            if not(l3): output.append([k1, k2])
        if not(l2): output.append([k1])
    
    return output

def makenested2(nesteddict, keylist,item=None):
    """ Insert item into nested dictionary, creating keys if required """
    currentlevel = nesteddict
    for i,key in enumerate(keylist[:-1]):
    	if not(key in currentlevel):
    		currentlevel[key] = {}
    	currentlevel = currentlevel[key]
    currentlevel[keylist[-1]] = item

    

def iternested2(nesteddict,previous = []):
	output = []
	for k in nesteddict.items():
		if isinstance(k[1],dict):
			output += iternested2(k[1],previous+[k[0]]) # Need to add these at the first level
		else:
			output.append(previous+[k[0]])
	return output




foo = {}
makenested(foo, ['a','x'])
makenested(foo, ['a','y'])
makenested(foo, ['a','z'])
makenested(foo, ['b','a','x'])
makenested(foo, ['b','a','y'])
foo['c'] = 1

foo2 = {}
makenested2(foo2, ['a','x'])
makenested2(foo2, ['a','y'])
makenested2(foo2, ['a','z'])
makenested2(foo2, ['b','a','x'])
makenested2(foo2, ['b','a','y'])
foo2['c'] = 1

print foo == foo2
print(foo2)

print(iternested(foo))
print iternested2(foo)
