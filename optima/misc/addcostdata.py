# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 08:56:53 2016
ADD COST DATA TO GM PROJECTS
@author: robynstuart
"""


from optima import odict
import csv

################
# Read in unit cost data from file
################
def readcostdata(costdatafilename=None):
    '''Read in cost data from an object or a spreadsheet'''
    
    allcostdata = odict()

    with open(costdatafilename, mode='r') as infile:
        reader = csv.DictReader(infile)

        for rows in reader:
            allcostdata[rows['Countries']] = odict()

            for column, value in rows.items():
                if column not in ['Countries','Region']:
                    if value:
                        allcostdata[rows['Countries']][column] = value

    return allcostdata


################
# Add unit cost data to an existing 2.0 project
################
def addcostdata(new=None, newinfile=None, outfile=None, costdatafilename=None, dosave=True):
    
    for prog in new.progsets[0].programs.values():

        # Figure out name of country
        allcostdata = readcostdata(costdatafilename=costdatafilename)
        countryname = new.name.split('_')[0]
        
        progname = prog.name
        if prog.name == 'SBCC + Condom': progname = 'Condoms & SBCC'
        if prog.name == 'HTC': progname = 'HIV testing'

        if prog.targetpars:
            unitcost = allcostdata[countryname][progname]
            prog.costcovfn.ccopars['unitcost'][0] = (unitcost, unitcost)
            
    return new


################
# Loop over a set of projects and add unit cost data to each 
################

from glob import glob
from os import sep
from optima import loadobj

def addallcostdata(projectpath=None, costdatafilename=None):

    # Define things
    worked = []
    failed = []
    allorigfiles = glob(projectpath+sep+'*'+'.prj')

    for f,origfile in enumerate(allorigfiles):

        print('Working on file %i of %i' % (f+1, len(allorigfiles)))

        try:
            newfile = origfile.replace('.prj', '_UC.prj')
    
            # Load file
            print('Loading data...')
            P = loadobj(origfile)
    
            # Update unit cost data
            print('Updating unit cost data...')
            P = addcostdata(new=P, costdatafilename=costdatafilename, dosave=False)
            
            # Save project
            P.save(filename=newfile) 
            worked.append(origfile)

        except Exception as E:
            failed.append(origfile+' | '+str(E))
    
    print('\n\n')
    print('Unit cost data updating succeeded for:')
    print('\n'.join(worked))
    print('\n\n')
    print('Unit cost data updating failed for:')
    print('\n'.join(failed))
    
    print('Done.')
    
