"""
OptimaWorkbook and related classes
Created by: SSQ
Started: 2-nov-2014
"""

import re
import xlsxwriter
from xlsxwriter.utility import *
from collections import OrderedDict


def abbreviate(param):
  words = re.sub('([^a-z0-9+]+)',' ',param.lower()).strip().split()
  short_param = ''
  for w in words:
    if re.match('[a-z]+',w):
      short_param += w[0]
    else:
      short_param += w
  return short_param.upper()

def years_range(data_start, data_end):
  return [str(x) for x in range(data_start, data_end+1)]

#class Assumption: #simulacrum of enums (no such thing in Python 2.7)
#  PERCENTAGE = 'percentage'
#  SCIENTIFIC = 'scientific'
#  NUMBER = 'number'
#  GENERAL = 'general'

""" the content of the data ranges (row names, column names, optional data and assumptions) """
class OptimaContent:
  def __init__(self, name, row_names, column_names, data = None):
    self.name = name
    self.row_names = row_names
    self.column_names = column_names
    self.data = data
    self.assumption = False
    self.programs = False
    self.row_levels = None
    self.row_format = OptimaFormats.GENERAL


  def set_row_format(self, row_format):
    self.row_format = row_format

  def has_data(self):
    return self.data != None

  def add_assumption(self):
    self.assumption = True

  def has_assumption(self):
    return self.assumption

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
  return OptimaContent(name, params, years_range(data_start, data_end))

""" 
every params array is a dictionary with at least these entries:
name - param name
acronym - param acronym
"""
def make_parameter_range(name, params):
  column_names = ['Short name', 'Long name']
  row_names = range(1, len(params)+1)
  coded_params = []
  for item in params:
    if type(item) is dict:
      item_name = item['name']
      acronym = item.get('acronym', abbreviate(item_name))
      coded_params.append([acronym, item_name])
    else:
      coded_params = [list((abbreviate(item), item)) for item in params]
  return OptimaContent(name, row_names, column_names, coded_params)

def make_constant_range(name, row_names, best_data):
  column_names = ['best', 'low', 'high']
  range_data = [[item, None, None] for item in best_data]
  return OptimaContent(name, row_names, column_names, range_data)

def make_ref_years_range(name, ref_range, data_start, data_end):
  params = ref_range.param_refs()
  return make_years_range(name, params, data_start, data_end)

""" the formats used in the workbook """
class OptimaFormats:
  BG_COLOR = '#B3DEE5'
  BORDER_COLOR = 'white'

  PERCENTAGE = 'percentage'
  DECIMAL_PERCENTAGE = 'decimal_percentage'
  SCIENTIFIC = 'scientific'
  NUMBER = 'number'
  GENERAL = 'general'

  def __init__(self, book):
    self.formats = {}
    self.book = book
    # locked formats
    self.formats['bold'] = self.book.add_format({'bold':1})
    # unlocked formats
    self.formats['unlocked'] = self.book.add_format({'locked':0, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
    self.formats['percentage'] = self.book.add_format({'locked':0, 'num_format':0x09, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
    self.formats['decimal_percentage'] = self.book.add_format({'locked':0, 'num_format':0x0a, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
    self.formats['scientific'] = self.book.add_format({'locked':0, 'num_format':0x0b, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
    self.formats['number'] = self.book.add_format({'locked':0, 'num_format':0x04, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
    self.formats['general'] = self.book.add_format({'locked':0, 'num_format':0x00, \
      'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})

  def write_block_name(self, sheet, name, row):
    sheet.write(row, 0, name, self.formats['bold'])

  def write_rowcol_name(self, sheet, row, col, name):
    sheet.write(row, col, name, self.formats['bold'])

  def write_option(self, sheet, row, col, name = 'OR'):
    sheet.write(row, col, name, self.formats['bold'])

  def write_unlocked(self, sheet, row, col, data, row_format = 'unlocked'):
    sheet.write(row, col, data, self.formats[row_format])

  def write_empty_unlocked(self, sheet, row, col, row_format = 'unlocked'):
    sheet.write_blank(row, col, None, self.formats[row_format])

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
  ROW_INTERVAL = 3
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
    #iterate over rows
    for i, names in enumerate(self.content.get_row_names()):
      start_col = self.data_range.first_col - len(names)
      #emit row name(s)
      for n, name in enumerate(names):
        formats.write_rowcol_name(self.sheet, current_row, start_col+n, name)
      #emit data if present
      if self.content.has_data():
        print self.content.data
        for j, item in enumerate(self.content.data[i]):
          formats.write_unlocked(self.sheet, current_row, self.data_range.first_col+j, item, self.content.row_format)
      else:
        for j in range(self.data_range.num_cols):
          formats.write_empty_unlocked(self.sheet, current_row, self.data_range.first_col+j, self.content.row_format)
      #emit assumption
      if self.content.has_assumption():
        formats.write_option(self.sheet, current_row, self.data_range.last_col+1)
        formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col+2, \
          self.content.row_format)
      #emit programs
      if self.content.has_programs(): 
        formats.write_option(self.sheet, current_row, self.data_range.last_col+1)
        formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col+5, OptimaFormats.GENERAL)
        for num in [7,8,10,11]:
          formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col+num, OptimaFormats.PERCENTAGE)
      current_row+=1
      if num_levels > 1 and ((i+1) % num_levels)==0: # shift between the blocks
        current_row +=1

    return current_row + TitledRange.ROW_INTERVAL # for spacing

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
                 ('drug', 'Injecting behavior'), \
                 ('partner', 'Partnerships'), \
                 ('trans', 'Transitions'), \
                 ('constants', 'Constants'), \
                 ('discosts', 'Disutilities & costs'), \
                 ('macroecon', 'Macroeconomics')])

  def __init__(self, name, pops, progs, data_start = 2000, data_end = 2015, econ_data_start = 2015, econ_data_end = 2030, verbose = 2):
    self.name = name
    self.pops = pops
    self.progs = progs
    self.data_start = data_start
    self.data_end = data_end
    self.econ_data_start = econ_data_start
    self.econ_data_end = econ_data_end
    self.verbose = verbose
    self.book = None
    self.sheets = None
    self.formats = None
    self.current_sheet = None
    self.prog_range = None
    self.pop_range = None

    self.npops = len(pops)
    self.nprogs = len(progs)

  def ref_pop_range(self):
    return self.pop_range.param_refs()

  def ref_prog_range(self):
    return self.prog_range.param_refs()

  def emit_content_block(self, name, current_row, row_names, column_names, data = None, row_format = OptimaFormats.GENERAL, \
    assumption = False, programs = False, row_levels = False):
    content = OptimaContent(name, row_names, column_names, data)
    content.set_row_format(row_format)
    if assumption:
      content.add_assumption()
    if programs:
      content.add_programs()
    if row_levels:
      content.add_row_levels()
    the_range = TitledRange(self.current_sheet, current_row, content)
    current_row = the_range.emit(self.formats)
    return current_row


  def emit_matrix_block(self, name, current_row, row_names):
    content = make_matrix_range(name, row_names)
    the_range = TitledRange(self.current_sheet, current_row, content)
    current_row = the_range.emit(self.formats)
    return current_row

  def emit_constants_block(self, name, current_row, row_names, best_data, row_format = OptimaFormats.GENERAL):
    content = make_constant_range(name, row_names, best_data)
    content.set_row_format(row_format)
    the_range = TitledRange(self.current_sheet, current_row, content)
    current_row = the_range.emit(self.formats)
    return current_row


  def emit_years_block(self, name, current_row, row_names, row_format = OptimaFormats.GENERAL, \
    assumption = False, programs = False, row_levels = False):
    content = make_years_range(name, row_names, self.data_start, self.data_end)
    content.set_row_format(row_format)
    if assumption:
      content.add_assumption()
    if programs:
      content.add_programs()
    if row_levels:
      content.add_row_levels()
    the_range = TitledRange(self.current_sheet, current_row, content)
    current_row = the_range.emit(self.formats)
    return current_row
  

  def emit_ref_years_block(self, name, current_row, ref_range, row_format = OptimaFormats.GENERAL, \
    assumption = None, programs = False, row_levels = False):
    content = make_ref_years_range(name, ref_range, self.data_start, self.data_end)
    content.set_row_format(row_format)
    if assumption:
      content.add_assumption()
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

    current_row = self.emit_ref_years_block('Coverage', current_row, self.prog_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)

    self.formats.write_option(self.current_sheet, current_row, 10, "AND EITHER")
    current_row +=2

    current_row = self.emit_ref_years_block('Total program cost', current_row, self.prog_range, row_format = OptimaFormats.SCIENTIFIC, assumption = True)

    self.formats.write_option(self.current_sheet, current_row, 10)
    current_row +=2

    current_row = self.emit_ref_years_block('Unit cost', current_row, self.prog_range, row_format = OptimaFormats.NUMBER, assumption = True)

  def generate_demo(self):
    self.current_sheet = self.sheets['demo']
    self.current_sheet.protect()
    current_row = 0

    current_row = self.emit_ref_years_block('Population size', current_row, self.pop_range, row_format = OptimaFormats.SCIENTIFIC, assumption = True, row_levels = True)
    current_row = self.emit_ref_years_block('HIV prevalence', current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True, row_levels = True)

  def generate_epi(self):
    self.current_sheet = self.sheets['epi']
    self.current_sheet.protect()
    current_row = 0

    for name in ['Percentage of people who die from non-HIV-related causes per year', \
    'Prevalence of any ulcerative STIs', 'Prevalence of any discharging STIs', 'Tuberculosis prevalence']:
      current_row = self.emit_ref_years_block(name, current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True, programs = True)

  def generate_opid(self):
    self.current_sheet = self.sheets['opid']
    self.current_sheet.protect()
    current_row = 0

    for name in ['Number of HIV tests per year', 'Number of diagnoses per year', 'Modeled estimate of new infections per year', \
    'Modeled estimate of HIV prevalence', 'Number of AIDS-related deaths', 'Number of people initiating ART each year']:
      current_row = self.emit_years_block(name, current_row, ['Total'], row_format = OptimaFormats.NUMBER, assumption = True)

  def generate_txrx(self):
    self.current_sheet = self.sheets['txrx']
    self.current_sheet.protect()
    current_row = 0

    current_row = self.emit_years_block('Percentage of population tested for HIV in the last 12 months', current_row, ['Total'], row_format = OptimaFormats.PERCENTAGE, assumption = True, programs = True)
    current_row = self.emit_years_block('Probability of a person with CD4 <200 being tested per year', current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True, programs = True)
    current_row = self.emit_years_block('Number of people on first-line treatment', current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True, programs = True)
    current_row = self.emit_years_block('Number of people on second-line treatment', current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True, programs = True)
    current_row = self.emit_years_block('Percentage of women on PMTCT (Option B/B+)', current_row, ['Total'], row_format = OptimaFormats.PERCENTAGE, assumption = True, programs = True)
    current_row = self.emit_ref_years_block('Birth rate (births/woman/year)', current_row, self.pop_range, row_format = OptimaFormats.NUMBER, assumption = True, programs = True)
    current_row = self.emit_years_block('Percentage of HIV-positive women who breastfeed', current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True, programs = True)

  def generate_sex(self):
    self.current_sheet = self.sheets['sex']
    self.current_sheet.protect()
    current_row = 0
    names_formats = [('Number of acts with regular partners per person per year', OptimaFormats.GENERAL), \
    ('Number of acts with casual partners per person per year', OptimaFormats.GENERAL), \
    ('Number of acts with commercial partners per person per year', OptimaFormats.GENERAL), \
    ('Percentage of people who used a condom at last act with regular partners', OptimaFormats.PERCENTAGE), \
    ('Percentage of people who used a condom at last act with casual partners', OptimaFormats.PERCENTAGE), \
    ('Percentage of people who used a condom at last act with commercial partners', OptimaFormats.PERCENTAGE), \
    ('Percentage of males who have been circumcised', OptimaFormats.PERCENTAGE)]

    for (name, row_format) in names_formats:
      current_row = self.emit_ref_years_block(name, current_row, self.pop_range, row_format = row_format, assumption = True, programs = True)

  def generate_drug(self):
    self.current_sheet = self.sheets['drug']
    self.current_sheet.protect()
    current_row = 0
    names_formats_ranges = [('Average number of injections per person per year', OptimaFormats.GENERAL, self.ref_pop_range()), \
    ('Percentage of people who receptively shared a needle at last injection', OptimaFormats.PERCENTAGE, ['Average']), \
    ('Percentage of people who inject drugs who are on opiate substitution therapy', OptimaFormats.PERCENTAGE, ['Average'])]

    for (name, row_format, row_range) in names_formats_ranges:
      current_row = self.emit_years_block(name, current_row, row_range, row_format = row_format, assumption = True, programs = True)

  def generate_partner(self):
    self.current_sheet = self.sheets['partner']
    self.current_sheet.protect()
    current_row = 0
    names = ['Interactions between regular partners', 'Interactions between casual partners', \
    'Interactions between commercial partners', 'Interactions between people who inject drugs']

    for name in names:
      current_row = self.emit_matrix_block(name, current_row, self.ref_pop_range())

  def generate_trans(self):
    self.current_sheet = self.sheets['trans']
    self.current_sheet.protect()
    current_row = 0
    names = ['Age-related population transitions (average number of years before movement)', \
    'Risk-related population transitions (average number of years before movement)']

    for name in names:
      current_row = self.emit_matrix_block(name, current_row, self.ref_pop_range())

  def generate_constants(self):
    self.current_sheet = self.sheets['constants']
    self.current_sheet.protect()
    self.current_sheet.set_column(1,1,40)
    current_row = 0

    names_rows_data_format = [('Interaction-related transmissibility (% per act)', \
      ['Heterosexual insertive', 'Heterosexual receptive', 'Homosexual insertive', 'Homosexual receptive', \
      'Injecting', 'Mother-to-child (breastfeeding)','Mother-to-child (non-breastfeeding)'], \
      [0.0004, 0.0010, 0.0006, 0.0050, 0.0030, 0.05, 0.03], OptimaFormats.DECIMAL_PERCENTAGE), \
    ('Relative disease-related transmissibility', \
      ['Acute infection','CD4(>500)','CD4(350-500)','CD4(200-350)','CD4(<200)'], \
      [10,1,1,1,3.8], OptimaFormats.NUMBER), \
    ('Disease progression rate (% per year)', \
      ['Acute to CD4(>500)','CD4(500) to CD4(350-500)','CD4(350,500) to CD4(200-350)','CD4(200-350) to CD4(200)'], \
      [1.00, 0.25, 0.25, 0.50], OptimaFormats.PERCENTAGE), \
    ('Treatment recovery rate (% per year)', \
      ['CD4(350-500) to CD4 (>500)','CD4(200-350) to CD4(350-500)','CD4(<200) to CD4(200-350)'], \
      [0.45, 0.70, 0.36], OptimaFormats.PERCENTAGE), \
    ('Treatment failure rate (% per year)', \
      ['First-line treatment','Second-line treatment'], [0.2,0.1], OptimaFormats.PERCENTAGE), \
    ('Death rate (% mortality per year)', \
      ['Acute infection','CD4(>500)','CD4(350-500)','CD4(200-350)','CD4(<200)','On treatment','Tuberculosis cofactor'], \
      [0, 0.0005, 0.0010, 0.01, 0.49, 0.04, 0.02], OptimaFormats.DECIMAL_PERCENTAGE), \
    ('Relative transmissibility', \
      ['Condom','Circumcision','Diagnosis behavior change','STI cofactor increase','Opiate substitution therapy','PMTCT','ARV Treatment'], \
      [0.05, 0.30, 0.65, 3.50, 0.05, 0.05, 0.30], OptimaFormats.PERCENTAGE)]

    for (name, row_names, data, format) in names_rows_data_format:
      current_row = self.emit_constants_block(name, current_row, row_names, data, format)

  def generate_discosts(self):
    self.current_sheet = self.sheets['discosts']
    self.current_sheet.protect()
    self.current_sheet.set_column(1,1,40)
    current_row = 0

    names_rows_data_format = [('Disutility weights', \
      ['Untreated HIV, acute','Untreated HIV, CD4(>500)','Untreated HIV, CD4(350-500)','Untreated HIV, CD4(200-350)', \
      'Untreated HIV, CD4(<200)','Treated HIV'], [0.05, 0.10, 0.15, 0.22, 0.55, 0.05], OptimaFormats.NUMBER), \
    ('HIV-related health care costs (excluding treatment)', \
      ['Acute infection','CD4(>500)','CD4(350-500)','CD4(200-350)','CD4(<200)'], [0, 0, 1000, 5000, 50000], OptimaFormats.GENERAL), \
    ('Social mitigation costs', \
      ['Acute infection', 'CD4(>500)', 'CD4(350-500)', 'CD4(200-350)', 'CD4(<200)'], [0, 0, 0, 1000, 8000], OptimaFormats.GENERAL)]
    for (name, row_names, data, format) in names_rows_data_format:
      current_row = self.emit_constants_block(name, current_row, row_names, data, format)

  def generate_macroecon(self):
    self.current_sheet = self.sheets['macroecon']
    self.current_sheet.protect()
    current_row = 0

    names = ['Gross domestic product', 'Government revenue', 'Government expenditure', \
    'Total domestic and international health expenditure', 'General government health expenditure', \
    'Domestic HIV spending', 'Global Fund HIV commitments', 'PEPFAR HIV commitments', \
    'Other international HIV commitments', 'Private HIV spending']

    econ_years_range = years_range(self.econ_data_start, self.econ_data_end)
    for name in names:
      current_row = self.emit_content_block(name, current_row, ['Total'], econ_years_range, assumption = True)

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
    self.generate_opid()
    self.generate_txrx()
    self.generate_sex()
    self.generate_drug()
    self.generate_partner()
    self.generate_trans()
    self.generate_constants()
    self.generate_discosts()
    self.generate_macroecon()
    self.book.close()







def makespreadsheet(name, pops, progs, datastart=2000, dataend=2015, econ_datastart=2015, econ_dataend=2030, verbose=2):
    """
    MAKESPREADSHEET
    
    Generate the Optima spreadsheet
    
    Version: 2014nov19
    """
    
    from printv import printv
    from dataio import templatepath

    printv("""Generating spreadsheet with parameters:
             name = %s, pops = %s, progs = %s, datastart = %s, dataend = %s, 
             econ_datastart = %s, econ_dataend = %s""" % (name, pops, progs, datastart, dataend, econ_datastart, econ_dataend), 1, verbose)
    path = templatepath(name)
    book = OptimaWorkbook(name, pops, progs, datastart, dataend, econ_datastart, econ_dataend)
    book.create(path)
    
    printv('  ...done making spreadsheet %s.' % path, 2, verbose)
    return path