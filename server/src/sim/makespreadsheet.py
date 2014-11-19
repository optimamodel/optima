"""
MAKESPREADSHEET

Version: 2014nov19
"""
from optima_workbook import OptimaWorkbook
from dataio import templatepath
from printv import printv

def makespreadsheet(name, pops, progs, datastart=2000, dataend=2015, econ_datastart=2015, econ_dataend=2030, verbose=2):

    printv("""Generating spreadsheet with parameters:
             name = %s, pops = %s, progs = %s, datastart = %s, dataend = %s, 
             econ_datastart = %s, econ_dataend = %s""" % (name, pops, progs, datastart, dataend, econ_datastart, econ_dataend), 1, verbose)
    path = templatepath(name)
    book = OptimaWorkbook(name, pops, progs, datastart, dataend, econ_datastart, econ_dataend)
    book.create(path)
    
    printv('  ...done making spreadsheet %s.' % path, 2, verbose)
    return path