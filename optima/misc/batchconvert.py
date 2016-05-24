'''
BATCHCONVERT 
Convert all pprojects in a directory from 1.0 to 2.0.
'''

from optima.misc import loaddata, convert1to2
from glob import glob
from os import sep

# Define things
projpath = 'Test' # MAY WANT TO CHANGE THIS
debug = False # MAY WANT TO SET TO TRUE

origext = '.json'
newext = '.prj'
worked = []
failed = []
allorigfiles = glob(projpath+sep+'*'+origext)

for f,origfile in enumerate(allorigfiles):
    print('Working on file %i of %i' % (f+1, len(allorigfiles)))
    try:
        basename = origfile.replace(origext, '')
        newfile = basename + newext

        # Figure out the paths and load the files
        print('Loading data...')
        D = loaddata(origfile)

        # Convert project
        print('Converting project...')
        E = convert1to2(old=D, outfile=newfile, autofit=True, dosave=False) # Don't save automatically
        
        # Save project
        E.name = basename
#        E.save(filename=newfile) 
        worked.append(origfile)
    except Exception as E:
        failed.append(origfile+' | '+str(E))
        if debug: raise E

print('\n\n')
print('The following projects converted successfully:')
print('\n'.join(worked))
print('\n\n')
print('The following projects FAILED MISERABLY:')
print('\n'.join(failed))

print('Done.')