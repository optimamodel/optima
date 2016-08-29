# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 18:39:31 2016

@author: David Kedziora
"""

from optima import defaultobjectives
from optima.geospatial import makesheet, makeproj, create, addproj, saveport, loadport, rungeo, export, plotgeo

if __name__ == '__main__':
    # Creating portfolio from subdivision spreadsheet.
    makesheet(projectpath='./geo/blantyre.prj', spreadsheetpath='./geo/BlantyreSplitBlank.xlsx', copies=2, refyear=2017)
    makeproj(projectpath='./geo/blantyre.prj', spreadsheetpath='./geo/BlantyreSplitFilled.xlsx', destination='./geo')
    create(filepaths=['./geo/Blantyre - District 1.prj','./geo/Blantyre - District 2.prj'])
    
    # Creating portfolio from projects (that already have BOCs).
    create(filepaths=['./geo/blantyre.prj'])
    addproj(filepaths=['./geo/balaka.prj'])   # Use addportfolio argument if not wanting to work with globals.
    saveport(filepath='./geo/blantyre-balaka.prt')    # Use portfolio argument if not wanting to work with globals.

    gaobjectives = defaultobjectives(verbose=0)
    gaobjectives['budget'] = 15000000.0 # Reset
    
    loadport(filepath='./geo/blantyre-balaka.prt')
    rungeo(objectives=gaobjectives, BOCtime=2)     # Use portfolio argument if not wanting to work with globals.
    export(filepath='./geo/blantyre-balaka-results.xlsx')
    plotgeo()