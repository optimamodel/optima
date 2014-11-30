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
        self.row_formats = None

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

    def set_row_levels(self, row_levels): # right now assume the row levels are hard coded, as it is only needed once
        self.row_levels = row_levels

    def set_row_formats(self, row_formats):
        self.row_formats = row_formats

    def has_row_formats(self):
        return self.row_formats != None

    def has_row_levels(self):
        return self.row_levels != None

    def get_row_names(self):
        if not self.has_row_levels():
            return [[name] for name in self.row_names]
        else:
            return [[name, level] for name in self.row_names for level in self.row_levels]

    def get_row_formats(self): #assume that the number of row_formats is same as the number of row_levels
        if not self.has_row_levels():
            return [self.row_format for name in self.row_names]
        else:
            if self.has_row_formats():
                return [row_format for name in self.row_names for row_format in self.row_formats]
            else:
                return [self.row_format for name in self.row_names for level in self.row_levels]

""" It's not truly pythonic, they cay, to have class methods """
def make_matrix_range(name, params):
    return OptimaContent(name, params, params)

def make_years_range(name, params, data_start, data_end):
    return OptimaContent(name, params, years_range(data_start, data_end))

""" 
every populations item is a dictionary is expected to have the following fields:
internal_name, short_name, name, male, female, injects, sexmen, sexwomen, sexworker, client
(3x str, 7x bool)
"""
def make_populations_range(name, items):
    column_names = ['Internal name','Short name','Long name','Male','Female','Injects','Sex with men', \
    'Sex with women','Sex worker','Client']
    row_names = range(1, len(items)+1)
    coded_params = []
    for item in items:
        if type(item) is dict:
            item_name = item['name']
            internal_name = item.get('internal_name', abbreviate(item_name))
            short_name = item.get('short_name', abbreviate(item_name))
            male = item.get('male', False)
            female = item.get('female', False)
            injects = item.get('injects',False)
            sexmen = item.get('sexmen',False) # WARNING need to update
            sexwomen = item.get('sexwomen',False)
            sexworker = item.get('injects',False)
            client = item.get('injects',False)      
        else: # backward compatibility :) might raise exception which is ok
            item_name = item
            internal_name = abbreviate(item_name)
            short_name = internal_name
            male = False
            female = False
            injects = False
            sexmen = False
            sexwomen = False
            sexworker = False
            client = False      
        coded_params.append([internal_name, short_name, item_name, male, female, injects, sexmen, sexwomen, sexworker, client])
    return OptimaContent(name, row_names, column_names, coded_params)

""" 
every programs item is a dictionary is expected to have the following fields:
internal_name, short_name, name, saturating
(3x str, 1x bool)
"""
def make_programs_range(name, items):
    column_names = ['Internal name','Short name','Long name','Saturating']
    row_names = range(1, len(items)+1)
    coded_params = []
    for item in items:
        if type(item) is dict:
            item_name = item['name']
            internal_name = item.get('internal_name', abbreviate(item_name))
            short_name = item.get('short_name', abbreviate(item_name))
            saturating = item.get('saturating', False)
        else: # backward compatibility :) might raise exception which is ok
            item_name = item
            internal_name = abbreviate(item_name)
            short_name = internal_name
            saturating = False      
        coded_params.append([internal_name, short_name, item_name, saturating])
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
        self.formats['rc_title'] = {}
        self.formats['rc_title']['right'] = self.book.add_format({'bold':1, 'align':'right'})
        self.formats['rc_title']['left'] = self.book.add_format({'bold':1, 'align':'left'})
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

    def write_rowcol_name(self, sheet, row, col, name, align = 'right'):
        sheet.write(row, col, name, self.formats['rc_title'][align])

    def write_option(self, sheet, row, col, name = 'OR'):
        sheet.write(row, col, name, self.formats['bold'])

    #special processing for bool values (to keep the content separate from representation)
    def write_unlocked(self, sheet, row, col, data, row_format = 'unlocked'):
        if type(data)==bool:
            bool_data = 'TRUE' if data else 'FALSE'
            sheet.write(row, col, bool_data, self.formats[row_format])
        else:
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
    def param_refs(self, sheet_name, column_number = 1):
        par_range = range(self.first_row, self.last_row +1)
        return [ "='%s'!%s" % (sheet_name, self.get_cell_address(row, self.first_col + column_number)) for row in par_range ]


class TitledRange:
    FIRST_COL = 2
    ROW_INTERVAL = 3

    def __init__(self, sheet, first_row, content):
        self.sheet = sheet
        self.content = content
        first_data_col = TitledRange.FIRST_COL
        num_data_rows = len(self.content.row_names)

        if self.content.has_row_levels():
            first_data_col +=1
            num_data_rows *= len(self.content.row_levels)
            num_data_rows += len(self.content.row_names)-1
        self.data_range = SheetRange(first_row+2, first_data_col, num_data_rows, len(self.content.column_names))
        self.first_row = first_row

    def num_rows(self):
        return self.data_range.num_rows + 2

    """ emits the range and returns the new current row in the given sheet """
    def emit(self, formats, rc_title_align = 'right'): #only important for row/col titles
        #top-top headers
        formats.write_block_name(self.sheet, self.content.name, self.first_row)
        if self.content.has_programs():
            for p in range(4):
                formats.write_rowcol_name(self.sheet, self.first_row, self.data_range.last_col + 5 + p*6 + 1, 'Zero coverage')
                formats.write_rowcol_name(self.sheet, self.first_row, self.data_range.last_col + 5 + p*6 + 3, 'Full coverage')

        #headers
        for i, name in enumerate(self.content.column_names):
            formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.first_col+i,name, rc_title_align)
            if self.content.has_assumption():
                formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+2, 'Assumption')
            if self.content.has_programs():
                for p in range(4):
                    formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+ 5 + p*6, 'Program %s' % (p+1))
                    formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+ 5 + p*6 + 1, 'Min')
                    formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+ 5 + p*6 + 2, 'Max')
                    formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+ 5 + p*6 + 3, 'Min')
                    formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+ 5 + p*6 + 4, 'Max')


        current_row = self.data_range.first_row
        num_levels = len(self.content.row_levels) if self.content.has_row_levels() else 1

        #iterate over rows, incrementing current_row as we go
        for i, names_format in enumerate(zip(self.content.get_row_names(), self.content.get_row_formats())):
            names, row_format = names_format
            start_col = self.data_range.first_col - len(names)
            #emit row name(s)
            for n, name in enumerate(names):
                formats.write_rowcol_name(self.sheet, current_row, start_col+n, name)
            #emit data if present
            if self.content.has_data():
                #print self.content.data
                for j, item in enumerate(self.content.data[i]):
                    formats.write_unlocked(self.sheet, current_row, self.data_range.first_col+j, item, row_format)
            else:
                for j in range(self.data_range.num_cols):
                    formats.write_empty_unlocked(self.sheet, current_row, self.data_range.first_col+j, row_format)
            #emit assumption
            if self.content.has_assumption():
                formats.write_option(self.sheet, current_row, self.data_range.last_col+1)
                formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col+2, \
                row_format)
            #emit programs
            if self.content.has_programs(): 
                for p in range(4):
                   for num in range(5):
                    formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col + 5 + p*6 + num, OptimaFormats.PERCENTAGE)
            current_row+=1
            if num_levels > 1 and ((i+1) % num_levels)==0: # shift between the blocks
                current_row +=1
        #done! return the new current_row plus spacing
        return current_row + TitledRange.ROW_INTERVAL # for spacing

    def param_refs(self, column_number = 1):
        return self.data_range.param_refs(self.sheet.get_name(), column_number)

class OptimaWorkbook:
    sheet_names = OrderedDict([('pp','Populations & programs'), \
    ('cc', 'Cost & coverage'), \
    ('demo', 'Demographics & HIV prevalence'), \
    ('opid', 'Optional indicators'), \
    ('epi', 'Other epidemiology'), \
    ('txrx', 'Testing & treatment'), \
    ('sex', 'Sexual behavior'), \
    ('drug', 'Injecting behavior'), \
    ('partner', 'Partnerships'), \
    ('trans', 'Transitions'), \
    ('constants', 'Constants'), \
    ('discosts', 'Disutilities & costs'), \
    ('macroecon', 'Macroeconomics')])

    def __init__(self, name, pops, progs, data_start = 2000, data_end = 2015, econ_data_start = 2015, \
        econ_data_end = 2030, verbose = 2):
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
        self.ref_pop_range = None
        self.ref_pop_range_internal = None
        self.ref_prog_range = None

        self.npops = len(pops)
        self.nprogs = len(progs)

    def emit_content_block(self, name, current_row, row_names, column_names, data = None, \
        row_format = OptimaFormats.GENERAL, assumption = False, programs = False, row_levels = None):
        content = OptimaContent(name, row_names, column_names, data)
        content.set_row_format(row_format)
        if assumption:
            content.add_assumption()
        if programs:
            content.add_programs()
        if row_levels is not None:
            content.set_row_levels(row_levels)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row


    def emit_matrix_block(self, name, current_row, row_names, column_names = None):
        if column_names is None:
            column_names = row_names
        content = OptimaContent(name, row_names, column_names)
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
        assumption = False, programs = False, row_levels = None, row_formats = None):
        content = make_years_range(name, row_names, self.data_start, self.data_end)
        content.set_row_format(row_format)
        if assumption:
            content.add_assumption()
        if programs:
            content.add_programs()
        if row_levels is not None:
            content.set_row_levels(row_levels)
        if row_formats is not None:
            content.set_row_formats(row_formats)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row


    def emit_ref_years_block(self, name, current_row, ref_range, row_format = OptimaFormats.GENERAL, \
        assumption = None, programs = False, row_levels = None, row_formats = None):
        content = make_ref_years_range(name, ref_range, self.data_start, self.data_end)
        content.set_row_format(row_format)
        if assumption:
            content.add_assumption()
        if programs:
            content.add_programs()
        if row_levels is not None:
            content.set_row_levels(row_levels)
        if row_formats is not None:
            content.set_row_formats(row_formats)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row

    def generate_pp(self):
        pp_sheet = self.sheets['pp']
        pp_sheet.protect()
        pp_sheet.set_column(2,2,15)
        pp_sheet.set_column(3,3,15)
        pp_sheet.set_column(4,4,40)
        pp_sheet.set_column(7,7,12)
        pp_sheet.set_column(8,8,12)
        pp_sheet.set_column(9,9,12)
        current_row = 0

        pop_content = make_populations_range('Populations', self.pops)
        self.pop_range = TitledRange(pp_sheet, current_row, pop_content) # we'll need it for references
        current_row = self.pop_range.emit(self.formats, 'left')

        prog_content = make_programs_range('Programs', self.progs)
        self.prog_range = TitledRange(pp_sheet, current_row, prog_content) # ditto
        current_row = self.prog_range.emit(self.formats, 'left')

        self.ref_pop_range = self.pop_range.param_refs()
        self.ref_pop_range_internal = self.pop_range.param_refs(0)

        self.ref_prog_range = self.prog_range.param_refs()

    def generate_cc(self):
        row_levels = ['Coverage', 'Cost']
        self.current_sheet = self.sheets['cc']
        self.current_sheet.protect()
        current_row = 0

        current_row = self.emit_years_block('Cost & coverage', current_row, self.ref_prog_range, row_formats = [OptimaFormats.PERCENTAGE,OptimaFormats.NUMBER], assumption = True, row_levels = row_levels)

    def generate_demo(self):
        row_levels = ['high', 'best', 'low']
        self.current_sheet = self.sheets['demo']
        self.current_sheet.protect()
        current_row = 0

        current_row = self.emit_ref_years_block('Population size', current_row, self.pop_range, row_format = OptimaFormats.SCIENTIFIC, assumption = True, row_levels = row_levels)
        current_row = self.emit_ref_years_block('HIV prevalence', current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True, row_levels = row_levels)

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

        current_row = self.emit_ref_years_block('Percentage of population tested for HIV in the last 12 months', current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True, programs = True)
        current_row = self.emit_years_block('Probability of a person with CD4 <200 being tested per year', current_row, ['Average'], row_format = OptimaFormats.GENERAL, assumption = True, programs = True)
        current_row = self.emit_years_block('Number of people on first-line treatment', current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True, programs = True)
        current_row = self.emit_years_block('Number of people on second-line treatment', current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True, programs = True)
        current_row = self.emit_ref_years_block('Percentage of people covered by pre-exposure prophylaxis', current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True, programs = True)
        current_row = self.emit_ref_years_block('Percentage of people covered by post-exposure prophylaxis', current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True, programs = True)
        current_row = self.emit_years_block('Number of women on PMTCT (Option B/B+)', current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True, programs = True)
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
        ('Percentage of males who have been circumcised', OptimaFormats.PERCENTAGE), \
        ('Number of voluntary medical male circumcisions performed', OptimaFormats.GENERAL)]

        for (name, row_format) in names_formats:
            current_row = self.emit_ref_years_block(name, current_row, self.pop_range, row_format = row_format, assumption = True, programs = True)

    def generate_drug(self):
        self.current_sheet = self.sheets['drug']
        self.current_sheet.protect()
        current_row = 0
        names_formats_ranges = [('Average number of injections per person per year', OptimaFormats.GENERAL, self.ref_pop_range), \
        ('Percentage of people who receptively shared a needle at last injection', OptimaFormats.PERCENTAGE, ['Average']), \
        ('Number of people who inject drugs who are on opiate substitution therapy', OptimaFormats.GENERAL, ['Average'])]

        for (name, row_format, row_range) in names_formats_ranges:
            current_row = self.emit_years_block(name, current_row, row_range, row_format = row_format, assumption = True, programs = True)

    def generate_partner(self):
        self.current_sheet = self.sheets['partner']
        self.current_sheet.protect()
        current_row = 0
        names = ['Interactions between regular partners', 'Interactions between casual partners', \
        'Interactions between commercial partners', 'Interactions between people who inject drugs']

        for name in names:
            current_row = self.emit_matrix_block(name, current_row, self.ref_pop_range, self.ref_pop_range_internal)

    def generate_trans(self):
        self.current_sheet = self.sheets['trans']
        self.current_sheet.protect()
        current_row = 0
        names = ['Age-related population transitions (average number of years before movement)', \
        'Risk-related population transitions (average number of years before movement)']

        for name in names:
            current_row = self.emit_matrix_block(name, current_row, self.ref_pop_range, self.ref_pop_range_internal)

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
        ['Condom','Circumcision','Diagnosis behavior change','STI cofactor increase','Opiate substitution therapy',\
        'PMTCT','ARV Treatment', 'Pre-exposure prophylaxis', 'Post-exposure prophylaxis'], \
        [0.05, 0.30, 0.65, 3.50, 0.05, 0.05, 0.30, 0.5, 0.5], OptimaFormats.PERCENTAGE)]

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
