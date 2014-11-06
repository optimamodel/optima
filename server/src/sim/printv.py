# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 18:06:21 2014

@author: cliffk
"""

def printv(string,thisverbose=0,verbose=2):
    """
    Optionally print a message and automatically indent
    """
    if verbose>=thisverbose: # Only print if sufficiently verbose
        indents = '  '*thisverbose # Create automatic indenting
        print('%s%s' % (indents,string)) # Actually print