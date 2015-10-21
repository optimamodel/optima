import sqlite3
import os
import cPickle

def makedb():
	try:
		os.remove('optima.db')
	except:
		pass

	conn = sqlite3.connect('optima.db')
	c = conn.cursor()
	c.execute('CREATE TABLE projects(uuid TEXT UNIQUE, data BLOB)')
	c.execute('CREATE TABLE simboxes(uuid TEXT UNIQUE, data BLOB)')
	c.execute('CREATE TABLE sims(uuid TEXT UNIQUE, data BLOB)')
	c.execute('CREATE TABLE calibrations(uuid TEXT UNIQUE, data BLOB)')
	c.execute('CREATE TABLE programsets(uuid TEXT UNIQUE, data BLOB)')

	conn.commit()
	conn.close()

def getconn():
	return sqlite3.connect('optima.db')

def sanitize(table_name):
	# Prevent SQL injection for table name substitution
    return ''.join( chr for chr in table_name if (chr.isalnum() or chr == '-'))

def retrieve(table,uuid):
	conn = getconn()
	c = conn.cursor()
	c.execute('SELECT data FROM %s WHERE %s.uuid = "%s"' % (sanitize(table),sanitize(table),sanitize(uuid)))
	d = c.fetchall()
	print sanitize(uuid)
	if len(d) > 1:
		print d
	datastr = str(d[0][0])
	conn.commit()
	conn.close()
	return cPickle.loads(datastr)


def store(table,uuid,data):
	# data needs to be storable as a cPickle string
	datastr = cPickle.dumps(data)
	conn = getconn()
	c = conn.cursor()
	c.execute('INSERT OR REPLACE INTO %s (uuid, data) VALUES (?,?)' % (sanitize(table)),(uuid,datastr))
	conn.commit()
	conn.close()

	
# x = ['asdf',1]
# print x
# makedb()
# store('projects','1d83',x)
# x2 = retrieve('projects','1d83')
# print x2
# y = ['asdf',2]
# store('projects','1d83',y)
# x3 = retrieve('projects','1d83')
# print x3