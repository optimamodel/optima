import numpy

def dict_equal(d1,d2):
	# Check if two dictionaries contain the same stuff

	# Check that they're the same type
	if type(d1) != type(d2):
		return False

	if d1 is None and d2 is None:
		return True

	# If they are dictionaries, check all of their fields
	if isinstance(d1,dict):
		if d1.keys() != d2.keys():
			return False
		else:
			return all([dict_equal(d1[k],d2[k]) for k in d1.keys()])
	
	# Vector reduction for ndarrays
	elif isinstance(d1,numpy.ndarray):
		is_eq = d1 == d2
		if isinstance(is_eq,numpy.ndarray):
			return (d1 == d2).all()
		elif isinstance(is_eq,bool):
			return is_eq
		else:
			raise Exception('Unknown returned data type!')

	# Direct equality
	elif isinstance(d1,(list,tuple,float,int,str,unicode)):
		return d1 == d2

	else:
		raise Exception("Do not know how to compare objects of type %s" % type(d1))






	def tojson(x):
	    """ Convert an object to JSON-serializable format, handling e.g. Numpy arrays """
	    from numpy import ndarray, isnan

	    if isinstance(x, dict):
	        return dict( (k, tojson(v)) for k,v in x.iteritems() )
	    elif isinstance(x, (list, tuple)):
	        return type(x)( tojson(v) for v in x )
	    elif isinstance(x, ndarray):
	        return {"np_array":[tojson(v) for v in x.tolist()], "np_dtype":x.dtype.name}
	    elif isinstance(x, float) and isnan(x):
	        return None
	    else:
	        return x
