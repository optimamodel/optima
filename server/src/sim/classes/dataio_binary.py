import cPickle
import gzip
import numpy

def save(obj,fname):
	# Using numpy. WARNING - this will add a .npz extension
	#numpy.savez_compressed(fname,obj)

	# Using cPickle
	with gzip.GzipFile(fname, 'wb') as file_data:
		cPickle.dump(obj,file_data)

def load(fname):
	# Using numpy
	#obj = numpy.load(fname)['arr_0'].tolist() 

	# Using cPickle
	with gzip.GzipFile(fname, 'rb') as file_data:
		obj = cPickle.load(file_data)
	
	return obj
