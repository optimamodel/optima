"""
METADATA

Version: 2015sep03 by cliffk
"""

from uuid import uuid4
from datetime import datetime
from time import mktime
from utils import run

version = 2.0



class Metadata(object):
    ''' Store all metadata for an Optima project '''
    
    
    def __init__(self, name='default'):
        ''' Create the metadata '''
        self.name = name
        self.uuid = uuid4()
        self.created = datetime.today()
        self.modified = datetime.today()
        self.version = version
        try:
            self.gitbranch = run('git rev-parse --abbrev-ref HEAD').rstrip('\n')
            self.gitversion = run('git rev-parse HEAD').rstrip('\n')
        except:
            self.gitbranch = 'Git branch information not retrivable'
            self.gitversion = 'Git version information not retrivable'
            import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
        return None
    
    
    
    def __repr__(self):
        ''' Print out useful information when called '''
        output = '\n'
        output += '   Project name: %s\n'    % self.name
        output += ' Optima version: %0.1f\n' % self.version
        output += '   Date created: %s\n'    % self.getdate(which='created')
        output += '  Date modified: %s\n'    % self.getdate(which='modified')
        output += '     Git branch: %s\n'    % self.gitbranch
        output += '    Git version: %s\n'    % self.gitversion
        output += '           UUID: %s\n'    % self.uuid
        return output
    
    
    
    def getdate(self, which='modified', fmt='str'):
        ''' Return either the date created or modified ("which") as either a str or int ("fmt") '''
        
        dateformat = '%Y-%b-%d %H:%M:%S'
        
        if which=='created': dateobj = self.created
        elif which=='modified': dateobj = self.modified
        else: raise Exception('"which=%s" not understood; must be "created" or "modified"' % which)
        
        if fmt=='str': return dateobj.strftime(dateformat) # Return string representation of time
        elif fmt=='int': return mktime(dateobj.timetuple()) # So ugly!! But it works -- return integer representation of time
        else: raise Exception('"fmt=%s" not understood; must be "str" or "int"' % fmt)
    
    
    
    def setdate(self):
        ''' Update the last modified date '''
        self.modified = datetime.today()
        return None