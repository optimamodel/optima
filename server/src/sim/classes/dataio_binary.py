import cPickle
import gzip

def save(obj,fname):
	with gzip.GzipFile(fname, 'wb') as file_data:
		cPickle.dump(obj,file_data)

def load(fname):
	with gzip.GzipFile(fname, 'rb') as file_data:
		obj = cPickle.load(file_data)
	return obj

