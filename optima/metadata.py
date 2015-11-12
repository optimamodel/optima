"""
METADATA

Version: 2015sep03 by cliffk
"""





class Metadata(object):
    ''' Store all metadata for an Optima project '''
    
    
    def __init__(self):
        ''' Create the metadata '''

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
