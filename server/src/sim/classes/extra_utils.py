import numpy
import sys
sys.path.append('../tests')
import add_optima_paths
import region
import sim
import simbox

def dict_equal(d1,d2,verbose=2,keyname=''):
	# Check if two dictionaries contain the same stuff

	# Check that they're the same type
	if isinstance(d1,str):
		d1 = unicode(d1)
	if isinstance(d2,str):
		d2 = unicode(d2)

	if type(d1) != type(d2):
		if verbose:
			print 'Types of %s and %s are different: they are %s and %s' % (d1,d2,type(d1),type(d2))
		return False

	if isinstance(d1,sim.Sim) or isinstance(d1,simbox.SimBox) or isinstance(d1,region.Region):
		return dict_equal(d1.todict(),d2.todict())

	if d1 is None and d2 is None:
		if verbose:
			print '%s and %s are None (keyname=%s)' % (d1,d2,keyname)
		return True

	# If they are dictionaries, check all of their fields
	if isinstance(d1,dict):
		if d1.viewkeys() != d2.viewkeys():
			if verbose:
				print 'Keys do not match: d1=%s,d2=%s' % (d1.keys(),d2.keys())
			return False
		else:
			return all([dict_equal(d1[k],d2[k],keyname=k) for k in d1.keys() if k is not 'UUID']) # Need to skip the UUID
	
	# Vector reduction for ndarrays
	elif isinstance(d1,numpy.ndarray):
		is_eq = (d1 == d2)
		if isinstance(is_eq,numpy.ndarray): # Why is this necessary sometimes...
			is_eq = (d1 == d2).all()
		elif not isinstance(is_eq,bool):
			raise Exception('Unknown returned data type!')
		if verbose and not is_eq:
			print 'Numpy array mismatch'
		return is_eq

	elif isinstance(d1,float):
		if numpy.isnan(d1) and numpy.isnan(d2):
			return true
		else:
			return
	# We might have a list of ndarrays 
	elif isinstance(d1,list):
		if len(d1) != len(d2):
			print "List length doesn't match - (keyname=%s)" % (keyname)
			return False
		rval = all([dict_equal(d1[x],d2[x]) for x in xrange(0,len(d1))]) 
		if not rval:
			print d1[1]
			print d2[1]
			print "List items don't match - (keyname=%s)" % (keyname)
		return rval
	# Direct equality
	elif isinstance(d1,(tuple,int,str,unicode)):
		return d1 == d2
	else:
		raise Exception("Do not know how to compare objects of type %s" % type(d1))
