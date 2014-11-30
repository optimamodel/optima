def printv(string, thisverbose=1, verbose=2):
    """
    Optionally print a message and automatically indent.
    """
    if verbose>=thisverbose: # Only print if sufficiently verbose
        indents = '  '*thisverbose # Create automatic indenting
        print('%s%s' % (indents,string)) # Actually print