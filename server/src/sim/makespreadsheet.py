"""
MAKESPREADSHEET

Version: 2014oct28
"""
import os
from loadspreadsheet import loadspreadsheet
from optima_workbook import OptimaWorkbook
from dataio import templatepath

def makespreadsheet(name, pops, progs, datastart=2000, dataend=2015, \
  econ_datastart=2015, econ_dataend=2030, verbose=2):

  if verbose >=1: 
    print("""Generating spreadsheet with parameters:
             name = %s, pops = %s, progs = %s, datastart = %s, dataend = %s, 
             econ_datastart = %s, econ_dataend = %s""" % \
             (name, pops, progs, datastart, dataend, econ_datastart, econ_dataend))
    path = templatepath(name)
    book = OptimaWorkbook(name, pops, progs, datastart, dataend, econ_datastart, econ_dataend)
    book.create(path)
    
    loadspreadsheet(path)
    if verbose>=2: print('  ...done making spreadsheet %s.' % path)
    return path