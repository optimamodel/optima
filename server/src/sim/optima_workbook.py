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


def abbreviate(param):
  words = re.sub('([^a-z0-9+]+)',' ',param.lower()).strip().split()
  short_param = ''
  for w in words:
    if re.match('[a-z]+',w):
      short_param += w[0]
    else:
      short_param += w
  return short_param.upper()


class OptimaContent:
  def __init__(self, name, row_names, column_names, data = None):
    self.name = name
    self.row_names = row_names
    self.column_names = column_names
    self.data = data

  def has_data(self):
    return self.data != None

""" It's not truly pythonic, they cay, to have class methods """
def make_matrix_range(name, params):
  return OptimaContent(name, params, params)

def make_years_range(name, params, data_start, data_end):
  years_range = [str(x) for x in range(data_start, data_end+1)]
  return OptimaContent(name, params, years_range)

def make_parameter_range(name, params):
  column_names = ['Short name', 'Long name']
  row_names = range(1, len(params))
  coded_params = [list((abbreviate(item), item)) for item in params]
  return OptimaContent(name, row_names, column_names, coded_params)


class OptimaFormats:
  def __init__(self, book):
    self.formats = {}
    self.book = book
    self.formats['unlocked'] = self.book.add_format({'locked':0, 'bg_color':'#B3DEE5','border':1, 'border_color':'white'})
    self.formats['bold'] = self.book.add_format({'bold':1})

  def write_block_name(self, sheet, name, row):
    sheet.write(row, 0, name, self.formats['bold'])

  def write_rowcol_name(self, sheet, row, col, name):
    sheet.write(row, col, name, self.formats['bold'])

  def write_unlocked(self, sheet, row, col, data):
    sheet.write(row, col, data, self.formats['unlocked'])

  def write_empty_unlocked(self, sheet, row, col):
    sheet.write_blank(row, col, None, self.formats['unlocked'])


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

class TitledRange:
  FIRST_COL = 2
  def __init__(self, first_row, content):
    self.data_range = SheetRange(first_row+2, TitledRange.FIRST_COL, len(content.row_names), len(content.column_names))
    self.content = content
    self.first_row = first_row

  def num_rows(self):
    return self.data_range.num_rows + 2

  """ emits the range and returns the new current row in the given sheet """
  def emit(self, sheet, formats):
    formats.write_block_name(sheet, self.content.name, self.first_row)
    for i, name in enumerate(self.content.column_names):
      formats.write_rowcol_name(sheet, self.first_row+1, TitledRange.FIRST_COL+i,name)
    for i, name in enumerate(self.content.row_names):
      formats.write_rowcol_name(sheet, self.data_range.first_row+i, self.data_range.first_col-1, name)
      if self.content.has_data():
        for j, item in enumerate(self.content.data[i]):
          formats.write_unlocked(sheet, self.data_range.first_row+i, self.data_range.first_col+j, item)
      else:
        for j in data_range.num_cols:
          formats.write_empty_unlocked(sheet, self.data_range.first_row+i, self.data_range.first_col+j)
    return self.first_row + self.num_rows() + 1 # for spacing

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

  def __init__(self, name, pops, progs, data_start = 2000, data_end = 2015, verbose = 2):
    self.name = name
    self.pops = pops
    self.progs = progs
    self.data_start = data_start
    self.data_end = data_end
    self.verbose = verbose
    self.book = None
    self.sheets = None
    self.formats = None

    self.npops = len(pops)
    self.nprogs = len(progs)
#    self.coded_pops = OrderedDict([(abbreviate(item), item) for item in self.pops])
#    self.coded_progs = OrderedDict([(abbreviate(item), item) for item in self.progs])

#  def write_block_name(self, sheet, name, row):
#    sheet.write(row, 0, name, self.formats['bold'])

#  def write_rowcol_name(self, sheet, row, col, name):
#    sheet.write(row, col, name, self.formats['bold'])

#  def write_unlocked(self, sheet, row, col, data):
#    sheet.write(row, col, data, self.formats['unlocked'])

#  def write_empty_unlocked(self, sheet, row, col, data):
#    sheet.write_blank(row, col, None, self.formats['unlocked'])

  def generate_pp(self):
    pp_sheet = self.sheets['pp']
    pp_sheet.protect()
    pp_sheet.set_column(2,2,15)
    pp_sheet.set_column(3,3,40)
    current_row = 0

    pop_content = make_parameter_range('Populations', self.pops)
    titled_pop_range = TitledRange(current_row, pop_content)
    current_row = titled_pop_range.emit(pp_sheet, self.formats)

    prog_content = make_parameter_range('Programs', self.progs)
    titled_prog_range = TitledRange(current_row, prog_content)
    current_row = titled_prog_range.emit(pp_sheet, self.formats)

#    first_col = 2
#    self.write_block_name(pp_sheet, 'Populations', current_row)
#    self.write_rowcol_name(pp_sheet, current_row+1, first_col,'Short name')
#    self.write_rowcol_name(pp_sheet, current_row+1, first_col+1,'Long name')

#    pop_range = SheetRange(current_row+2, first_col, self.npops, 2)
##    pop_range_name = "'%s'!%s" % (OptimaWorkbook.sheet_names['pp'], pop_range.get_address())
##    if self.verbose >=1:
##      print "PopulationsRange = %s", pop_range_name
##    self.book.define_name('PopulationsRange',pop_range_name)

#    for i, item in enumerate(self.coded_pops):
#      self.write_rowcol_name(pp_sheet, pop_range.first_row+i, pop_range.first_col-1, i+1)
#      self.write_unlocked(pp_sheet, pop_range.first_row+i, pop_range.first_col, item)
#      self.write_unlocked(pp_sheet, pop_range.first_row+i, pop_range.first_col+1, self.coded_pops[item])

#    current_row += 2 + pop_range.num_rows + 1

#    self.write_block_name(pp_sheet, 'Programs', current_row)
#    self.write_rowcol_name(pp_sheet, current_row+1, first_col,'Short name')
#    self.write_rowcol_name(pp_sheet, current_row+1, first_col+1,'Long name')

#    prog_range = SheetRange(current_row+2, first_col, self.nprogs, 2)
##    self.book.define_name('ProgramsRange',"'%s!%s" % (OptimaWorkbook.sheet_names['pp'], prog_range.get_address()))
#    for i, item in enumerate(self.coded_progs):
#      self.write_rowcol_name(pp_sheet, prog_range.first_row+i, prog_range.first_col-1, i+1)
#      self.write_unlocked(pp_sheet, prog_range.first_row+i, prog_range.first_col, item)
#      self.write_unlocked(pp_sheet, prog_range.first_row+i, prog_range.first_col+1, self.coded_progs[item])

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
    self.formats = OptimaFormats(self.book)
#    self.formats = {}
#    self.formats['unlocked'] = self.book.add_format({'locked':0, 'bg_color':'#B3DEE5','border':1, 'border_color':'white'})
#    self.formats['bold'] = self.book.add_format({'bold':1})
    self.sheets = {}
    for name in OptimaWorkbook.sheet_names:
      self.sheets[name] = self.book.add_worksheet(OptimaWorkbook.sheet_names[name])
    self.generate_pp()
    self.book.close()

