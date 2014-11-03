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

class Assumption: #simulacrum of enums (no such thing in Python 2.7)
  PERCENTAGE = 'percentage'
  SCIENTIFIC = 'scientific'
  NUMBER = 'number'

""" the content of the data ranges (row names, column names, optional data and assumptions) """
class OptimaContent:
  def __init__(self, name, row_names, column_names, data = None):
    self.name = name
    self.row_names = row_names
    self.column_names = column_names
    self.data = data
    self.assumption = None
    self.programs = False
    self.row_levels = None

  def has_data(self):
    return self.data != None

  def add_assumption(self, assumption):
    self.assumption = assumption

  def has_assumption(self):
    return self.assumption != None

  def add_programs(self):
    self.programs = True

  def has_programs(self):
    return self.programs

  def add_row_levels(self): # right now assume the row levels are hard coded, as it is only needed once
    self.row_levels = ['high', 'best', 'low']

  def has_row_levels(self):
    return self.row_levels != None

  def get_row_names(self):
    if not self.has_row_levels():
      return [[name] for name in self.row_names]
    else:
      return [[name, level] for name in self.row_names for level in self.row_levels]

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

def make_ref_years_range(name, ref_range, data_start, data_end):
  params = ref_range.param_refs()
  return make_years_range(name, params, data_start, data_end)

""" the formats used in the workbook """
class OptimaFormats:
  BG_COLOR = '#B3DEE5'
  BORDER_COLOR = 'white'
  def __init__(self, book):
    self.formats = {}
    self.book = book
    self.formats['unlocked'] = self.book.add_format({'locked':0, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
    self.formats['bold'] = self.book.add_format({'bold':1})
    self.formats['percentage'] = self.book.add_format({'locked':0, 'num_format':0x09, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
    self.formats['scientific'] = self.book.add_format({'locked':0, 'num_format':0x0b, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
    self.formats['number'] = self.book.add_format({'locked':0, 'num_format':0x04, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})

  def write_block_name(self, sheet, name, row):
    sheet.write(row, 0, name, self.formats['bold'])

  def write_rowcol_name(self, sheet, row, col, name):
    sheet.write(row, col, name, self.formats['bold'])

  def write_option(self, sheet, row, col, name = 'OR'):
    sheet.write(row, col, name, self.formats['bold'])

  def write_unlocked(self, sheet, row, col, data):
    sheet.write(row, col, data, self.formats['unlocked'])

  def write_empty_unlocked(self, sheet, row, col):
    sheet.write_blank(row, col, None, self.formats['unlocked'])

  """ assumption: scientific, percentage or number """
  def write_empty_assumption(self, sheet, row, col, assumption):
    sheet.write_blank(row, col, None, self.formats[assumption])


class SheetRange:
  def __init__(self, first_row, first_col, num_rows, num_cols):
    self.first_row = first_row
    self.first_col = first_col

    self.num_rows = num_rows
    self.num_cols = num_cols

    self.last_row = self.first_row + self.num_rows -1
    self.last_col = self.first_col + self.num_cols -1

    self.start = self.get_cell_address(self.first_row, self.first_col)
    self.end = self.get_cell_address(self.last_row, self.last_col)

  def get_address(self):
    return '%s:%s' % (self.start, self.end)

  def get_cell_address(self, row, col):
    return xl_rowcol_to_cell(row, col, row_abs = True, col_abs = True)

  """ gives the list of references to the entries in the row names (which are parameters) """
  def param_refs(self, sheet_name):
    par_range = range(self.first_row, self.last_row +1)
    return [ "='%s'!%s" % (sheet_name, self.get_cell_address(row, self.first_col)) for row in par_range ]


class TitledRange:
  FIRST_COL = 2
  def __init__(self, sheet, first_row, content):
    self.sheet = sheet
    self.content = content
    first_data_col = TitledRange.FIRST_COL
    if self.content.has_row_levels():
      first_data_col +=1
    num_data_rows = len(self.content.row_names)
    if self.content.has_row_levels():
      num_data_rows *= len(self.content.row_levels)
      num_data_rows += len(self.content.row_names)-1
    self.data_range = SheetRange(first_row+2, first_data_col, num_data_rows, len(self.content.column_names))
    self.first_row = first_row

  def num_rows(self):
    return self.data_range.num_rows + 2

  """ emits the range and returns the new current row in the given sheet """
  def emit(self, formats):
    formats.write_block_name(self.sheet, self.content.name, self.first_row)
    if self.content.has_programs():
      formats.write_rowcol_name(self.sheet, self.first_row, self.data_range.last_col + 7, 'Zero coverage')
      formats.write_rowcol_name(self.sheet, self.first_row, self.data_range.last_col + 10, 'Full coverage')

    for i, name in enumerate(self.content.column_names):
      formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.first_col+i,name)
    if self.content.has_assumption():
      formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+2, 'Assumption')
    if self.content.has_programs():
      formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+5, 'Programs')
      formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+7, 'Min')
      formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+8, 'Max')
      formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+10, 'Min')
      formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+11, 'Max')


    current_row = self.data_range.first_row
    num_levels = len(self.content.row_levels) if self.content.has_row_levels() else 1
    for i, names in enumerate(self.content.get_row_names()):
      start_col = self.data_range.first_col - len(names)
      for n, name in enumerate(names):
        formats.write_rowcol_name(self.sheet, current_row, start_col+n, name)
      if self.content.has_data():
        for j, item in enumerate(self.content.data[i]):
          formats.write_unlocked(self.sheet, current_row, self.data_range.first_col+j, item)
      else:
        for j in range(self.data_range.num_cols):
          formats.write_empty_unlocked(self.sheet, current_row, self.data_range.first_col+j)
      if self.content.has_assumption():
        formats.write_option(self.sheet, current_row, self.data_range.last_col+1)
        formats.write_empty_assumption(self.sheet, current_row, self.data_range.last_col+2, \
          self.content.assumption)
      if self.content.has_programs(): #so far assumption seems to also be present in this case and with the same format
        formats.write_option(self.sheet, current_row, self.data_range.last_col+1)
        for num in [5,7,8,10,11]:
          formats.write_empty_assumption(self.sheet, current_row, self.data_range.last_col+num, \
            self.content.assumption)
      current_row+=1
      if num_levels > 1 and ((i+1) % num_levels)==0: # shift between the blocks
        current_row +=1

    return current_row + 1 # for spacing

  def param_refs(self):
    return self.data_range.param_refs(self.sheet.get_name())

class OptimaWorkbook:
  sheet_names = OrderedDict([('pp','Populations & programs'), \
                 ('cc', 'Cost & coverage'), \
                 ('demo', 'Demographics & HIV prevalence'), \
                 ('epi', 'Other epidemiology'), \
                 ('opid', 'Optional indicators'), \
                 ('txrx', 'Testing & treatment'), \
                 ('sex', 'Sexual behavior'), \
                 ('drug', 'Drug behavior'), \
                 ('partner', 'Partnerships'), \
                 ('trans', 'Transitions'), \
                 ('constants', 'Constants'), \
                 ('consts', 'Costs & disutilities'), \
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
    self.current_sheet = None

    self.npops = len(pops)
    self.nprogs = len(progs)

  def emit_ref_years_block(self, name, current_row, ref_range, assumption = None, programs = False, row_levels = False):
    content = make_ref_years_range(name, ref_range, self.data_start, self.data_end)
    if assumption is not None:
      content.add_assumption(assumption)
    if programs:
      content.add_programs()
    if row_levels:
      content.add_row_levels()
    the_range = TitledRange(self.current_sheet, current_row, content)
    current_row = the_range.emit(self.formats)
    return current_row

  def generate_pp(self):
    pp_sheet = self.sheets['pp']
    pp_sheet.protect()
    pp_sheet.set_column(2,2,15)
    pp_sheet.set_column(3,3,40)
    current_row = 0

    pop_content = make_parameter_range('Populations', self.pops)
    self.pop_range = TitledRange(pp_sheet, current_row, pop_content) # we'll need it for references
    current_row = self.pop_range.emit(self.formats)

    prog_content = make_parameter_range('Programs', self.progs)
    self.prog_range = TitledRange(pp_sheet, current_row, prog_content) # ditto
    current_row = self.prog_range.emit(self.formats)

  def generate_cc(self):
    self.current_sheet = self.sheets['cc']
    self.current_sheet.protect()
    current_row = 0

    current_row = self.emit_ref_years_block('Coverage', current_row, self.prog_range, Assumption.PERCENTAGE)

    self.formats.write_option(self.current_sheet, current_row, 10, "AND EITHER")
    current_row +=2

    current_row = self.emit_ref_years_block('Total program cost', current_row, self.prog_range, Assumption.SCIENTIFIC)

    self.formats.write_option(self.current_sheet, current_row, 10)
    current_row +=2

    current_row = self.emit_ref_years_block('Unit cost', current_row, self.prog_range, Assumption.NUMBER)

  def generate_demo(self):
    self.current_sheet = self.sheets['demo']
    self.current_sheet.protect()
    current_row = 0

    current_row = self.emit_ref_years_block('Population size', current_row, self.pop_range, Assumption.SCIENTIFIC, row_levels = True)
    current_row = self.emit_ref_years_block('HIV prevalence', current_row, self.pop_range, Assumption.PERCENTAGE, row_levels = True)

  def generate_epi(self):
    self.current_sheet = self.sheets['epi']
    self.current_sheet.protect()
    current_row = 0

    for name in ['Percentage of people who die from non-HIV-related causes per year', \
    'Prevalence of any ulcerative STIs', 'Prevalence of any discharging STIs', 'Tuberculosis prevalence']:
      current_row = self.emit_ref_years_block(name, current_row, self.pop_range, Assumption.PERCENTAGE, programs = True)

  def create(self, path):
    if self.verbose >=1: 
      print("""Creating workbook %s with parameters:
             npops = %s, nprogs = %s, data_start = %s, data_end = %s""" % \
             (path, self.npops, self.nprogs, self.data_start, self.data_end))
    self.book = xlsxwriter.Workbook(path)
    self.formats = OptimaFormats(self.book)
    self.sheets = {}
    for name in OptimaWorkbook.sheet_names:
      self.sheets[name] = self.book.add_worksheet(OptimaWorkbook.sheet_names[name])
    self.generate_pp()
    self.generate_cc()
    self.generate_demo()
    self.generate_epi()
    self.book.close()

