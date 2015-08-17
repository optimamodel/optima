# -*- coding: utf-8 -*-
"""
Loads the Malawi xlsx and converts into 32 regional (technically district) xlsx files.

Created on Thu Aug 10 19:00:00 2015

@author: David Kedziora, Romesh Abeysuriya
"""

import sys
sys.path.append('../tests')
import add_optima_paths
import defaults
import region
import programs
import loadworkbook
import re
from dataio import savedata, projectpath
from printv import printv
from numpy import arange
from copy import deepcopy
from updatedata import updatedata
from xlrd import open_workbook  # For opening Excel workbooks.
import xlsxwriter

#regionlist = ['Bali','Central Java','East Java','West Java','Jakarta','Papua','Riau']
#abbrevlist = ['B','CJ','EJ','WJ','J','P','R']

# Load Indonesia workbook.
inbook = open_workbook('./regions/Malawi_District 20150731.xlsx')
insheetnames = inbook.sheet_names()

summarysheet = inbook.sheet_by_name('Summary ')

# Determine region names from summary sheet.
districtlist = []
for rowindex in xrange(summarysheet.nrows):
    if summarysheet.cell_type(rowindex, 0) == 2:    # Check if 1st cell in row is a number.
        districtlist.append(summarysheet.cell_value(rowindex, 1))
print districtlist
print len(districtlist)
    
for districtname in districtlist:
    try:
        districtsheet = inbook.sheet_by_name(districtname)
        outbook = xlsxwriter.Workbook('./regions/Malawi ('+districtname+').xlsx')
        outsheet = outbook.add_worksheet(districtname)
        
        for rowindex in xrange(districtsheet.nrows):
            inrow = districtsheet.row(rowindex)
            for colindex in xrange(len(inrow)):
                celldata = districtsheet.cell_value(rowindex, colindex)
                outsheet.write(rowindex, colindex, celldata)
            
        outbook.close()
        
    except:
        print('There is a problem loading a district sheet.')
    


## Go through list of regions.
#for regid in xrange(len(regionlist)):
#    
#    abb = abbrevlist[regid]     # Each region corresponds with an abbreviation.
#
#    # Produce regional workbook.
#    outbook = xlsxwriter.Workbook('./regions/Indonesia ('+regionlist[regid]+').xlsx')
    
#    tag = ''
#    
#    # Iterate through sheets.
#    for insheetname in insheetnames:
#        insheet = inbook.sheet_by_name(insheetname)
#        outsheet = outbook.add_worksheet(insheetname)
#        
#        rowskip = 0
#        rowcorrect = 0
#        
#        # Iterate through rows. Check for certain phrases that start new sections of parsing.
#        for rowindex in xrange(insheet.nrows):
#            if insheet.cell_value(rowindex, 0) == 'Populations': tag = 'meta'
#            if insheet.cell_value(rowindex, 0) == 'Programs': rowcorrect = 0
#            if insheet.cell_value(rowindex, 0) == 'Cost & coverage': tag = 'data'
#            if insheet.cell_value(rowindex, 0) == 'Interactions between regular partners': tag = '2D'
#            if insheet.cell_value(rowindex, 0) == 'Interaction-related transmissibility (% per act)': tag = 'extra'
#                
#            inrow = insheet.row(rowindex)
#            
#            if (tag == 'meta' and not insheet.cell_value(rowindex, 2).endswith('('+abb+')') and insheet.cell_value(rowindex, 2).endswith(')')) or \
#            ((tag == 'data' or tag == '2D') and not insheet.cell_value(rowindex, 1).endswith('('+abb+')') and insheet.cell_value(rowindex, 1).endswith(')')):
#                rowskip += 1
#                rowcorrect += 1
#            else:
#                colskip = 0
#            
#                # Iterate through cells in a row.
#                for colindex in xrange(len(inrow)):
#                    if (tag == '2D' and not insheet.cell_value(1, colindex).endswith('('+abb+')') and insheet.cell_value(1, colindex).endswith(')')):
#                        colskip += 1
#                    else:
#                        # Copy and paste, skipping unnecessary rows and columns.
#                        celldata = insheet.cell_value(rowindex, colindex)
#                        if isinstance(celldata,unicode) and '('+abb+')' in celldata:
#                            celldata = celldata.replace(' ('+abb+')','')
#                        if (tag == 'meta' and colindex == 1 and insheet.cell_type(rowindex, colindex) == 2):
#                            outsheet.write(rowindex-rowskip, colindex-colskip, celldata-rowcorrect)                 # Adjust number ids for pops and progs.
#                        elif (tag == 'data' and insheet.cell_type(rowindex, colindex) == 2 and \
#                        ((insheet.cell_value(rowindex, 1) == 'ART' and insheet.cell_value(rowindex, 2) == 'Coverage') or \
#                        (insheet.cell_value(rowindex, 1) in ['ART','MGMT','M&E'] and insheet.cell_value(rowindex, 2) == 'Cost'))):
#                            outsheet.write(rowindex-rowskip, colindex-colskip, celldata/float(len(regionlist)))     # Divide national costs amongst regions. (Arguable with ART...)
#                        else:
#                            outsheet.write(rowindex-rowskip, colindex-colskip, celldata)
                
#    outbook.close()


## CODE FOR CONVERTING THE XLSX FILES TO JSON

def debracket(s):
    # Remove bracketed parts
    # 'FSW (B)' -> 'FSW'
    return str(re.sub('\(.*\)','',s)).strip()

def extract_pops(workbook_data):
    # Pops looks like
    # {'pops': {'client': [0, 1, 0, 0, 0, 0, 0],
    #   'female': [1, 0, 0, 0, 0, 0, 1],
    #   'injects': [0, 0, 0, 0, 1, 0, 0],
    #   'long': [u'Female sex workers (Bali)',
    #    u'Clients of sex workers (Bali)',
    #    u'Men who have sex with men (Bali)',
    #    u'Transgender individuals (Bali)',
    #    u'People who inject drugs (Bali)',
    #    u'Other males (Bali)',
    #    u'Other females (Bali)'],
    #   'male': [0, 1, 1, 0, 0, 1, 0],
    #   'sexmen': [1, 0, 1, 1, 0, 0, 1],
    #   'sexwomen': [0, 1, 0, 0, 0, 1, 0],
    #   'sexworker': [1, 0, 0, 0, 0, 0, 0],
    #   'short': [u'FSW (B)',
    #    u'Clients (B)',
    #    u'MSM (B)',
    #    u'Transgender (B)',
    #    u'PWID (B)',
    #    u'Males (B)',
    #    u'Females (B)']},
    #
    # Want haiti = {}
    #haiti['populations'] = [{u'name': u'Female sex workers', u'short_name': u'FSW', u'sexworker': True, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Clients of sex workers', u'short_name': u'Clients', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': True, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Men who have sex with men', u'short_name': u'MSM', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': False, u'male': True, u'sexwomen': False}, {u'name': u'Male Children (0-14)', u'short_name': u'Male children 0\u201014', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': False}, {u'name': u'Female Children (0-14)', u'short_name': u'Female Children 0-14', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Males (15-19)', u'short_name': u'Males 15-19', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Females (15-19)', u'short_name': u'Females 15-19', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Males (20-24)', u'short_name': u'Males 20-24', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Females (20-24)', u'short_name': u'Females 20-24', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Males (25-49)', u'short_name': u'Males 25-49', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Females (25-49)', u'short_name': u'Females 25-49', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Males (50+)', u'short_name': u'Males 50+', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Females (50+)', u'short_name': u'Females 50+', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}]
    
    popdict = workbook_data[0]['meta']['pops']
    out = []
    for i in xrange(0,len(popdict['client'])):
        entry = {}
        entry['name'] = debracket(popdict['long'][i])
        entry['short_name'] = debracket(popdict['short'][i])
        entry['sexworker'] =  bool(popdict['sexworker'][i])
        entry['injects'] =  bool(popdict['injects'][i])
        entry['sexmen'] =  bool(popdict['sexmen'][i])
        entry['client'] =  bool(popdict['client'][i])
        entry['female'] =  bool(popdict['female'][i])
        entry['male'] =  bool(popdict['male'][i])
        entry['sexwomen'] =  bool(popdict['sexwomen'][i])
        out.append(entry)
    return out

def extract_progs(workbook_data):
    progdict = programs.programs()
    proglist = [x['short_name'] for x in progdict]

    #workbook_progs = [x.split()[:-1] for x in workbook_data[0]['meta']['progs']['short']]
    #workbook_progs = [x for x in workbook_data[0]['meta']['progs']]
    
    # First, reconstct the names
    workbook_progs = []
    for i in xrange(0,len(workbook_data[0]['meta']['progs']['short'])):
        b = {'short':workbook_data[0]['meta']['progs']['short'][i],'long':workbook_data[0]['meta']['progs']['long'][i]}
        b['refname'] = debracket(b['short'])
        workbook_progs.append(b)

    out = []
    for prog in workbook_progs:
        a = progdict[proglist.index(prog['refname'])]
        a['name'] = prog['long']
        a['short_name'] = prog['short']
        out.append(a)

    return out

def fake_D(fname):
    # Create a D variable into which the XLSX file can be loaded
    # Strategy is NOT to load into OOP, but to load into original Optima
    # Then, OOP can load the optima JSON file, but the frontend can be used
    # by others to perform the calibration

    # First, get a list of the programs
    a = loadworkbook.loadworkbook(fname)
    inputpopulations = extract_pops(a)
    inputprograms = extract_progs(a)
    datastart = int(round(a[0]['epiyears'][0]))
    dataend = int(round(a[0]['epiyears'][-1]))
    nsims = 1 # Default is 5 in makeproject? Not sure what this value should be
    current_version = 4

    D = dict() # Data structure for saving everything
    D['plot'] = dict() # Initialize plotting data
    
    # Initialize options
    from setoptions import setoptions
    D['opt'] = setoptions()
    
    # Set up "G" -- general parameters structure
    D['G'] = dict()
    D['G']['version'] = current_version # so that we know the version of new project with regard to data structure
    projectname = fname.replace('./regions/','').replace('.xlsx','') 
    D['G']['projectname'] = projectname 
    D['G']['projectfilename'] = projectpath(projectname+'.prj')
    D['G']['workbookname'] = fname
    D['G']['npops'] = len(inputpopulations)
    D['G']['nprogs'] = len(inputprograms)
    D['G']['datastart'] = datastart
    D['G']['dataend'] = dataend
    D['G']['datayears'] = arange(D['G']['datastart'], D['G']['dataend']+1)
    D['G']['inputprograms'] = inputprograms # remember input programs with their possible deviations from standard parameter set (if entered from GUI). 

    D['G']['inputpopulations'] = inputpopulations # should be there as well, otherwise we cannot export project without data
    # Health states
    D['G']['healthstates'] = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
    D['G']['ncd4'] = len(D['G']['healthstates'])
    D['G']['nstates'] = 1+D['G']['ncd4']*5 # Five are undiagnosed, diagnosed, 1st line, failure, 2nd line, plus susceptible
    D['G']['sus']  = arange(0,1)
    D['G']['undx'] = arange(0*D['G']['ncd4']+1, 1*D['G']['ncd4']+1)
    D['G']['dx']   = arange(1*D['G']['ncd4']+1, 2*D['G']['ncd4']+1)
    D['G']['tx1']  = arange(2*D['G']['ncd4']+1, 3*D['G']['ncd4']+1)
    D['G']['fail'] = arange(3*D['G']['ncd4']+1, 4*D['G']['ncd4']+1)
    D['G']['tx2']  = arange(4*D['G']['ncd4']+1, 5*D['G']['ncd4']+1)
    for i,h in enumerate(D['G']['healthstates']): D['G'][h] = [D['G'][state][i] for state in ['undx', 'dx', 'tx1', 'fail', 'tx2']]
    
    return D

def makejson(region_name):
    # Make a project
    D = fake_D('./regions/Indonesia (%s).xlsx' % (region_name))

    # Load the XLSX file
    D = updatedata(D, workbookname=None, verbose=2, rerun=True)

    print D['programs']
    # Save a JSON
    savedata('./regions/indonesia_%s.json' % (region_name.lower()),D)

#for r in regionlist:
#    makejson(r)