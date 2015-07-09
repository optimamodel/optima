# -*- coding: utf-8 -*-
"""
Loads the Indonesian xlsx and converts into seven regional xlsx files.

Created on Thu Jul 09 19:11:49 2015

@author: David Kedziora
"""

import sys
sys.path.append('../tests')
import add_optima_paths
import region

from xlrd import open_workbook  # For opening Excel workbooks.
import xlsxwriter
from xlsxwriter.utility import *

# Load Indonesia workbook.
inbook = open_workbook('./regions/Indonesia2015regions-CK.xlsx')
insheetnames = inbook.sheet_names()

# Produce Bali workbook.
outbook = xlsxwriter.Workbook('./regions/Indonesia-Bali.xlsx')
for insheetname in insheetnames:
    insheet = inbook.sheet_by_name(insheetname)
    outsheet = outbook.add_worksheet(insheetname)
    for rowindex in xrange(insheet.nrows):
        inrow = insheet.row(rowindex)
        for colindex in xrange(len(inrow)):
            celldata = insheet.cell_value(rowindex, colindex)
            
            outsheet.write(rowindex, colindex, celldata)
            
outbook.close()

#r = region.Region('Indonesia (from XLSX)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
#r.makeworkbook('./regions/Indonesia2015regions-CK-test.xlsx') # Write to a dummy file for test purposes
#r.loadworkbook('./regions/Indonesia2015regions-CK.xlsx')