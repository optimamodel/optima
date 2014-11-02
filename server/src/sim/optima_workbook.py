"""
OptimaWorkbook and related classes
Created by: SSQ
Started: 2-nov-2014
"""

import re
import xlsxwriter
from xlsxwriter.utility import *
from collections import OrderedDict
import os
"""
class OptimaRange:
  def __init__(self, name, row_names, column_names):
    self.name = name
    self.row_names = row_names
    self.column_names = column_names

  def make_matrix_range(name, params):
    return new OptimaRange(name, params, params)

  def make_years_range(name, params, data_start, data_end):
    years_range = [str(x) for x in range(data_start, data_end+1)]
    return new OptimaRange(name, params, years_range)

  def make_program_range(name, params):
    column_names = ['Short name', 'Long name']
    return new OptimaRange(name, params, column_names)

  def make_population_range(name, params):
    column_names = ['Short name', 'Long name']
"""

class SheetRange:
  def __init__(self, first_row, first_col, num_rows, num_cols):
    self.first_row = first_row
    self.first_col = first_col
    self.num_rows = num_rows
    self.num_cols = num_cols
    self.last_row = self.first_row + self.num_rows -1
    self.last_col = self.first_col + self.num_cols -1
    self.start = xl_rowcol_to_cell(self.first_row, self.first_col, row_abs = True, col_abs = True)
    self.end = xl_rowcol_to_cell(self.last_row, self.last_col, row_abs = True, col_abs = True)
  def get_address(self):
    return '%s:%s' % (self.start, self.end)

class OptimaWorkbook:
  sheet_names = OrderedDict([('pp','Populations and programs'), \
                 ('cc', 'Cost and coverage'), \
                 ('epi', 'Epidemiology'), \
                 ('opid', 'Optional indicators'), \
                 ('txrx', 'Testing and treatment'), \
                 ('sex', 'Sexual behavior'), \
                 ('drug', 'Drug behavior'), \
                 ('partner', 'Partnerships'), \
                 ('trans', 'Transitions'), \
                 ('constants', 'Constants'), \
                 ('consts', 'Costs and disutilities'), \
                 ('macroecon', 'Macroeconomics')])

  def __init__(self, name, npops = 6, nprogs = 8, data_start = 2000, data_end = 2015, verbose = 2):
    self.name = name
    self.npops = npops
    self.nprogs = nprogs
    self.data_start = data_start
    self.data_end = data_end
    self.verbose = verbose
    self.book = None
    self.sheets = None
    self.formats = None

  def write_block_name(self, sheet, name, row):
    sheet.write(row, 0, name, self.formats['bold'])

  def write_rowcol_name(self, sheet, row, col, name):
    sheet.write(row, col, name, self.formats['bold'])

  def write_unlocked(self, sheet, row, col, data):
    sheet.write(row, col, data, self.formats['unlocked'])

  def generate_pp(self):
    pp_sheet = self.sheets['pp']
    pp_sheet.protect()
    current_row = 0
    first_col = 2
    self.write_block_name(pp_sheet, 'Populations', current_row)
    self.write_rowcol_name(pp_sheet, current_row+1, first_col,'Short name')
    self.write_rowcol_name(pp_sheet, current_row+1, first_col+1,'Long name')

    pop_range = SheetRange(current_row+2, first_col, self.npops, 2)
#    pop_range_name = "'%s'!%s" % (OptimaWorkbook.sheet_names['pp'], pop_range.get_address())
#    if self.verbose >=1:
#      print "PopulationsRange = %s", pop_range_name
#    self.book.define_name('PopulationsRange',pop_range_name)

    for i in range(pop_range.num_rows):
      self.write_rowcol_name(pp_sheet, pop_range.first_row+i, pop_range.first_col-1, i+1)
      self.write_unlocked(pp_sheet, pop_range.first_row+i, pop_range.first_col, "POP%s" % str(i+1))
      self.write_unlocked(pp_sheet, pop_range.first_row+i, pop_range.first_col+1, "Population %s" % str(i+1))

    current_row += 2 + pop_range.num_rows + 1

    self.write_block_name(pp_sheet, 'Programs', current_row)
    self.write_rowcol_name(pp_sheet, current_row+1, first_col,'Short name')
    self.write_rowcol_name(pp_sheet, current_row+1, first_col+1,'Long name')

    prog_range = SheetRange(current_row+2, first_col, self.nprogs, 2)
#    self.book.define_name('ProgramsRange',"'%s!%s" % (OptimaWorkbook.sheet_names['pp'], prog_range.get_address()))
    for i in range(prog_range.num_rows):
      self.write_rowcol_name(pp_sheet, prog_range.first_row+i, prog_range.first_col-1, i+1)
      self.write_unlocked(pp_sheet, prog_range.first_row+i, prog_range.first_col, "PRG%s" % str(i+1))
      self.write_unlocked(pp_sheet, prog_range.first_row+i, prog_range.first_col+1, "Program %s" % str(i+1))

  def generate_cc(self):
    cc_sheet = self.sheets['cc']
    cc_sheet.protect()
    current_row = 0


  def create(self, path):
    if self.verbose >=1: 
      print("""Creating workbook %s with parameters:
             npops = %s, nprogs = %s, data_start = %s, data_end = %s""" % \
             (path, self.npops, self.nprogs, self.data_start, self.data_end))
    self.book = xlsxwriter.Workbook(path)
    self.formats = {}
    self.formats['unlocked'] = self.book.add_format({'locked':0, 'bg_color':'#B3DEE5','border':1, 'border_color':'white'})
    self.formats['bold'] = self.book.add_format({'bold':1})
    self.sheets = {}
    for name in OptimaWorkbook.sheet_names:
      self.sheets[name] = self.book.add_worksheet(OptimaWorkbook.sheet_names[name])
    self.generate_pp()
    self.book.close()

