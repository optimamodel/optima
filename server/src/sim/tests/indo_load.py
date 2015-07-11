# -*- coding: utf-8 -*-
"""
Loads the Indonesian xlsx and converts into seven regional xlsx files.

Created on Thu Jul 09 19:11:49 2015

@author: David Kedziora, Romesh Abeysuriya
"""

import sys
sys.path.append('../tests')
import add_optima_paths

from xlrd import open_workbook  # For opening Excel workbooks.
import xlsxwriter

regionlist = ['Bali','Central Java','East Java','West Java','Jakarta','Papua','Riau']
abbrevlist = ['B','CJ','EJ','WJ','J','P','R']

# Load Indonesia workbook.
inbook = open_workbook('./regions/Indonesia2015regions-CK.xlsx')
insheetnames = inbook.sheet_names()

# Go through list of regions.
for regid in xrange(len(regionlist)):
    
    abb = abbrevlist[regid]     # Each region corresponds with an abbreviation.

    # Produce regional workbook.
    outbook = xlsxwriter.Workbook('./regions/Indonesia ('+regionlist[regid]+').xlsx')
    
    tag = ''
    
    # Iterate through sheets.
    for insheetname in insheetnames:
        insheet = inbook.sheet_by_name(insheetname)
        outsheet = outbook.add_worksheet(insheetname)
        
        rowskip = 0
        rowcorrect = 0
        
        # Iterate through rows. Check for certain phrases that start new sections of parsing.
        for rowindex in xrange(insheet.nrows):
            if insheet.cell_value(rowindex, 0) == 'Populations': tag = 'meta'
            if insheet.cell_value(rowindex, 0) == 'Programs': rowcorrect = 0
            if insheet.cell_value(rowindex, 0) == 'Cost & coverage': tag = 'data'
            if insheet.cell_value(rowindex, 0) == 'Interactions between regular partners': tag = '2D'
            if insheet.cell_value(rowindex, 0) == 'Interaction-related transmissibility (% per act)': tag = 'extra'
                
            inrow = insheet.row(rowindex)
            
            if (tag == 'meta' and not insheet.cell_value(rowindex, 2).endswith('('+abb+')') and insheet.cell_value(rowindex, 2).endswith(')')) or \
            ((tag == 'data' or tag == '2D') and not insheet.cell_value(rowindex, 1).endswith('('+abb+')') and insheet.cell_value(rowindex, 1).endswith(')')):
                rowskip += 1
                rowcorrect += 1
            else:
                colskip = 0
            
                # Iterate through cells in a row.
                for colindex in xrange(len(inrow)):
                    if (tag == '2D' and not insheet.cell_value(1, colindex).endswith('('+abb+')') and insheet.cell_value(1, colindex).endswith(')')):
                        colskip += 1
                    else:
                        # Copy and paste, skipping unnecessary rows and columns.
                        celldata = insheet.cell_value(rowindex, colindex)
                        if isinstance(celldata,unicode) and '('+abb+')' in celldata:
                            celldata = celldata.replace(' ('+abb+')','')
                        if (tag == 'meta' and colindex == 1 and insheet.cell_type(rowindex, colindex) == 2):
                            outsheet.write(rowindex-rowskip, colindex-colskip, celldata-rowcorrect)                 # Adjust number ids for pops and progs.
                        elif (tag == 'data' and insheet.cell_type(rowindex, colindex) == 2 and \
                        ((insheet.cell_value(rowindex, 1) == 'ART' and insheet.cell_value(rowindex, 2) == 'Coverage') or \
                        (insheet.cell_value(rowindex, 1) in ['ART','MGMT','M&E'] and insheet.cell_value(rowindex, 2) == 'Cost'))):
                            outsheet.write(rowindex-rowskip, colindex-colskip, celldata/float(len(regionlist)))     # Divide national costs amongst regions. (Arguable with ART...)
                        else:
                            outsheet.write(rowindex-rowskip, colindex-colskip, celldata)
                
    outbook.close()