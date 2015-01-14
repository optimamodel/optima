"""
Four little functions to get and set data from nested dictionaries. The first two were stolen from:
    http://stackoverflow.com/questions/14692690/access-python-nested-dictionary-items-via-a-list-of-keys

"getnested" will get the value for the given list of keys:
    getnested(foo, ['a','b'])

"setnested" will set the value for the given list of keys:
    setnested(foo, ['a','b'], 3)

"makenested" will recursively update a dictionary with the given list of keys:
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

def getnested(nesteddict, keylist, safe=False): 
    """ Get a value from a nested dictionary"""
    output = reduce(lambda d, k: d.get(k) if d else None if safe else d[k], keylist, nesteddict)
    return output

def setnested(nesteddict, keylist, value): 
    """ Set a value in a nested dictionary """
    getnested(nesteddict, keylist[:-1])[keylist[-1]] = value
    return None # Modify nesteddict in place

def makenested(nesteddict, keylist,item=None):
    """ Insert item into nested dictionary, creating keys if required """
    currentlevel = nesteddict
    for i,key in enumerate(keylist[:-1]):
    	if not(key in currentlevel):
    		currentlevel[key] = {}
    	currentlevel = currentlevel[key]
    currentlevel[keylist[-1]] = item

def iternested(nesteddict,previous = []):
	output = []
	for k in nesteddict.items():
		if isinstance(k[1],dict):
			output += iternested(k[1],previous+[k[0]]) # Need to add these at the first level
		else:
			output.append(previous+[k[0]])
	return output

