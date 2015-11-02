"""
METADATA

Version: 2015sep03 by cliffk
"""

from uuid import uuid4
from datetime import datetime
from utils import run

version = 2.0



class Metadata(object):
    ''' Store all metadata for an Optima project '''
    
    
    def __init__(self):
        ''' Create the metadata '''
        self.filename = None
        self.id = uuid4()
        self.created = datetime.today()
        self.modified = datetime.today()
        self.spreadsheetdate = 'Spreadsheet never loaded'
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
        ''' Print out useful information when called -- see also repr() for the project class'''
        output = '\n'
        output += '   Project name: %s\n'    % self.name
        output += '       Filename: %s\n'    % self.filename
        output += ' Optima version: %0.1f\n' % self.version
        output += '   Date created: %s\n'    % self.getdate(which='created')
        output += '  Date modified: %s\n'    % self.getdate(which='modified')
        output += '    Data loaded: %s\n'    % self.getdate(which='spreadsheetdate')
        output += '     Git branch: %s\n'    % self.gitbranch
        output += '    Git version: %s\n'    % self.gitversion
        output += '             ID: %s\n'    % self.id
        return output
