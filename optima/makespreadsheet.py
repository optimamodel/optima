"""
OptimaSpreadsheet and related classes
Created by: SSQ

Version: 2016jan18 by robyns
"""

import xlsxwriter
from xlsxwriter.utility import re, xl_rowcol_to_cell
from collections import OrderedDict
from utils import printv

default_datastart = 2000
default_dataend = 2020

def makespreadsheet(filename, pops, datastart=default_datastart, dataend=default_dataend, verbose=2):
    """ Generate the Optima spreadsheet -- the hard work is done by makespreadsheet.py """

    # An integer argument is given: just create a pops dict using empty entries
    if isinstance(pops, (int, float)):
        npops = pops
        pops = [] # Create real pops list
        for p in range(npops):
            pops.append({'short_name':'Pop %i'%(p+1), 'name':'Population %i'%(p+1), 'male':True, 'female':True, 'age_from':0, 'age_to':99}) # Must match make_populations_range definitions
    
    printv('Generating spreadsheet: pops=%i, datastart=%s, dataend=%s' % (len(pops), datastart, dataend), 1, verbose)

    book = OptimaSpreadsheet(filename, pops, datastart, dataend)
    book.create(filename)

    printv('  ...done making spreadsheet %s.' % filename, 2, verbose)
    return filename


def makeeconspreadsheet(filename, datastart=default_datastart, dataend=default_dataend, verbose=2):
    """ Generate the Optima economics spreadsheet -- the hard work is done by makespreadsheet.py """

    printv('Generating economics spreadsheet: start=%s, end=%i' % (datastart, dataend), 1, verbose)
    book = EconomicsSpreadsheet(filename, datastart, dataend)
    book.create(filename)

    printv('  ...done making economics spreadsheet %s.' % filename, 2, verbose)
    return filename




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
    return [x for x in range(data_start, data_end+1)]

class OptimaContent:
    """ the content of the data ranges (row names, column names, optional data and assumptions) """
    def __init__(self, name, row_names, column_names, data = None):
        self.name = name
        self.row_names = row_names
        self.column_names = column_names
        self.data = data
        self.assumption = False
        self.row_levels = None
        self.row_format = OptimaFormats.GENERAL
        self.row_formats = None
        self.assumption_properties = {'title':None, 'connector':'OR', 'columns':['Assumption']}

    def set_row_format(self, row_format):
        self.row_format = row_format

    def has_data(self):
        return self.data != None

    def add_assumption(self):
        self.assumption = True

    def has_assumption(self):
        return self.assumption

    def set_assumption_properties(self, assumption_properties):
        self.assumption_properties = assumption_properties

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

def make_populations_range(name, items):
    """ 
    every populations item is a dictionary is expected to have the following fields:
    short_name, name, male, female, age_from, age_to
    (3x str, 2x bool, 2x int)
    """
    column_names = ['Short name','Long name','Male','Female','Age from (years)', 'Age to (years)']
    row_names = range(1, len(items)+1)
    coded_params = []
    for item in items:
        if type(item) is dict:
            item_name = item['name']
            short_name = item.get('short_name', abbreviate(item_name))
            male = item.get('male', False)
            female = item.get('female', False)
            age_from = item.get('age_from',15)
            age_to = item.get('age_to',49)
        else: # backward compatibility :) might raise exception which is ok
            item_name = item
            short_name = abbreviate(item_name)
            male = False
            female = False
            age_from = 15
            age_to = 49
        coded_params.append([short_name, item_name, male, female, age_from, age_to])
    return OptimaContent(name, row_names, column_names, coded_params)

def make_constant_range(name, row_names, best_data, low_data, high_data):
    column_names = ['best', 'low', 'high']
    range_data = [[best, low, high] for (best, low, high) in zip(best_data, low_data, high_data)]
    return OptimaContent(name, row_names, column_names, range_data)

def make_ref_years_range(name, ref_range, data_start, data_end):
    params = ref_range.param_refs()
    return make_years_range(name, params, data_start, data_end)

def filter_by_properties(param_refs, base_params, the_filter):
    """
    filter parameter references by properties of the parameters.
    """
    result = []
    filter_set = set(the_filter.items())
    for (param_ref, param) in zip(param_refs, base_params):     
        if set(param.items()) & filter_set:
            result.append(param_ref)
    return result


class OptimaFormats:
    """ the formats used in the spreadsheet """
    originalblue = '#18C1FF'
    hotpink = '#FFC0CB'
    BG_COLOR = hotpink
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
        self.formats['center_bold'] = self.book.add_format({'bold':1, 'align':'center'})
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
        self.formats['info_header'] = self.book.add_format({'align':'center','valign':'vcenter', \
            'color':'#D5AA1D','fg_color':'#0E0655', 'font_size':20})
        self.formats['grey'] = self.book.add_format({'fg_color':'#EEEEEE', 'text_wrap':True})
        self.formats['info_url'] = self.book.add_format({'fg_color':'#EEEEEE', 'text_wrap':True, 'color':'blue','align':'center'})
        self.formats['grey_bold'] = self.book.add_format({'fg_color':'#EEEEEE','bold':True})


    def write_block_name(self, sheet, name, row):
        sheet.write(row, 0, name, self.formats['bold'])

    def write_rowcol_name(self, sheet, row, col, name, align = 'right'):
        sheet.write(row, col, name, self.formats['rc_title'][align])

    def write_option(self, sheet, row, col, name = 'OR'):
        sheet.write(row, col, name, self.formats['center_bold'])

    #special processing for bool values (to keep the content separate from representation)
    def write_unlocked(self, sheet, row, col, data, row_format = 'unlocked'):
        if type(data)==bool:
            bool_data = 'TRUE' if data else 'FALSE'
            sheet.write(row, col, bool_data, self.formats[row_format])
        else:
            sheet.write(row, col, data, self.formats[row_format])

    def write_empty_unlocked(self, sheet, row, col, row_format = 'unlocked'):
        sheet.write_blank(row, col, None, self.formats[row_format])

    def write_info_line(self, sheet, row, row_format='grey'):
        sheet.write_blank(row, 0, None, self.formats[row_format])
        return row+1

    def write_info_block(self, sheet, row, text, row_format = 'grey', row_height = None, add_line = True):
        if row_height:
            sheet.set_row(row, row_height)
        sheet.write(row, 0, text, self.formats[row_format])
        if add_line:
            return self.write_info_line(sheet, row+1)
        else:
            return row+1

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
    def emit(self, formats, rc_row_align = 'right', rc_title_align = 'right'): #only important for row/col titles
        #top-top headers
        formats.write_block_name(self.sheet, self.content.name, self.first_row)

        if self.content.has_assumption() and  self.first_row==0 and self.content.assumption_properties['title'] is not None:
            formats.write_rowcol_name(self.sheet, self.first_row, self.data_range.last_col+2, self.content.assumption_properties['title'])

        #headers
        for i, name in enumerate(self.content.column_names):
            formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.first_col+i,name, rc_title_align)
        if self.content.has_assumption():
            for index, col_name in enumerate(self.content.assumption_properties['columns']):
                formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.last_col+2+index, col_name)


        current_row = self.data_range.first_row
        num_levels = len(self.content.row_levels) if self.content.has_row_levels() else 1

        #iterate over rows, incrementing current_row as we go
        for i, names_format in enumerate(zip(self.content.get_row_names(), self.content.get_row_formats())):
            names, row_format = names_format
            start_col = self.data_range.first_col - len(names)
            #emit row name(s)
            for n, name in enumerate(names):
                formats.write_rowcol_name(self.sheet, current_row, start_col+n, name, rc_row_align)
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
                formats.write_option(self.sheet, current_row, self.data_range.last_col+1, \
                    name = self.content.assumption_properties['connector'])
                for index, col_name in enumerate(self.content.assumption_properties['columns']):
                    formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col+2+index, row_format)
            current_row+=1
            if num_levels > 1 and ((i+1) % num_levels)==0: # shift between the blocks
                current_row +=1
        #done! return the new current_row plus spacing
        return current_row + TitledRange.ROW_INTERVAL # for spacing

    def param_refs(self, column_number = 0):
        return self.data_range.param_refs(self.sheet.get_name(), column_number)

class EconomicsSpreadsheet:
    def __init__(self, name, data_start = default_datastart, data_end = default_dataend, verbose = 0):
        self.sheet_names = OrderedDict([
            ('instr', 'Instructions'),
            ('econ', 'Economics and costs')])
        self.name = name
        self.data_start = data_start
        self.data_end = data_end
        self.verbose = verbose
        self.book = None
        self.sheets = None
        self.formats = None
        self.current_sheet = None
        self.years_range = years_range(self.data_start, self.data_end)

    def emit_content_block(self, name, current_row, row_names, column_names, data = None,
        row_format = OptimaFormats.GENERAL, assumption = False, row_levels = None,
        assumption_properties = None):
        content = OptimaContent(name, row_names, column_names, data)
        content.set_row_format(row_format)
        if assumption:
            content.add_assumption()
        if assumption_properties:
            content.set_assumption_properties(assumption_properties)
        if row_levels is not None:
            content.set_row_levels(row_levels)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row

    def generate_instr(self):
        current_row = 0
        self.current_sheet.set_column('A:A',80)
        self.current_sheet.merge_range('A1:A3', 'OPTIMA ECONOMIC DATA', self.formats.formats['info_header'])
        current_row = 3
        current_row = self.formats.write_info_line(self.current_sheet, current_row)
        current_row = self.formats.write_info_block(self.current_sheet, current_row, row_height=65, text='Welcome to the spreadsheet for entering economic data into Optima. Uploading this spreadsheet is required if you wish to view estimates of the financial costs associated with epidemic projections. All rows are optional, but if you do enter data for a row, you must also enter a growth assumption. Please ask someone from the Optima development team if you need help, or use the default contact (info@optimamodel.com).')
        current_row = self.formats.write_info_block(self.current_sheet, current_row, text='For further details please visit: http://optimamodel.com/file/indicator-guide')

    def generate_econ(self):
        current_row = 0

        names = ['Consumer price index','Gross domestic product', 'Government revenue', 'Government expenditure', \
        'Total domestic and international health expenditure', 'General government health expenditure']

        assumption_properties = {'title':'Growth assumptions', 'connector':'AND', 'columns':['best','low','high']}

        for name in names:
            current_row = self.emit_content_block(name, current_row, ['Total'], self.years_range, assumption = True, \
                row_format = OptimaFormats.SCIENTIFIC, assumption_properties = assumption_properties)

        names_rows = [('HIV-related health care costs (excluding treatment)', \
        ['Acute infection','CD4(>500)','CD4(350-500)','CD4(200-350)','CD4(50-200)','CD4(<50)']), \
        ('Social mitigation costs', \
        ['Acute infection', 'CD4(>500)', 'CD4(350-500)', 'CD4(200-350)', 'CD4(50-200)','CD4(<50)'])]
        for (name, row_names) in names_rows:
            current_row = self.emit_content_block(name, current_row, row_names, self.years_range, assumption = True, \
                row_format = OptimaFormats.NUMBER, assumption_properties = assumption_properties)
                
    def create(self, path):
        if self.verbose >=1: 
            print("""Creating spreadsheet %s with parameters:
            npops = %s, data_start = %s, data_end = %s""" % \
            (path, self.npops, self.data_start, self.data_end))
        self.book = xlsxwriter.Workbook(path)
        self.formats = OptimaFormats(self.book)
        self.sheets = {}
        for name in self.sheet_names:
            self.sheets[name] = self.book.add_worksheet(self.sheet_names[name])
            self.current_sheet = self.sheets[name]
            getattr(self, "generate_%s" % name)() # this calls the corresponding generate function
        self.book.close()


class OptimaSpreadsheet:
    def __init__(self, name, pops, data_start = default_datastart, data_end = default_dataend, verbose = 0):
        self.sheet_names = OrderedDict([
            ('instr', 'Instructions'),
            ('meta','Populations'),
            ('popsize', 'Population size'),
            ('key', 'HIV prevalence'),
            ('epi', 'Other epidemiology'),
            ('opt', 'Optional indicators'),
            ('txrx', 'Testing & treatment'),
            ('casc', 'Cascade'),
            ('sex', 'Sexual behavior'),
            ('inj', 'Injecting behavior'),
            ('ptrans', 'Partnerships & transitions'),
            ('const', 'Constants')])
        self.name = name
        self.pops = pops
        self.data_start = data_start
        self.data_end = data_end
        self.verbose = verbose
        self.book = None
        self.sheets = None
        self.formats = None
        self.current_sheet = None
        self.pop_range = None
        self.ref_pop_range = None
        self.years_range = years_range(self.data_start, self.data_end)

        self.npops = len(pops)

    def emit_content_block(self, name, current_row, row_names, column_names, data = None,
        row_format = OptimaFormats.GENERAL, assumption = False, row_levels = None,
        assumption_properties = None):
        content = OptimaContent(name, row_names, column_names, data)
        content.set_row_format(row_format)
        if assumption:
            content.add_assumption()
        if assumption_properties:
            content.set_assumption_properties(assumption_properties)
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

    def emit_constants_block(self, name, current_row, row_names, best_data, low_data, high_data, 
        row_format = OptimaFormats.GENERAL):
        content = make_constant_range(name, row_names, best_data, low_data, high_data)
        content.set_row_format(row_format)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats, rc_row_align = 'left')
        return current_row

    def emit_years_block(self, name, current_row, row_names, row_format = OptimaFormats.GENERAL,
        assumption = False, row_levels = None, row_formats = None):
        content = make_years_range(name, row_names, self.data_start, self.data_end)
        content.set_row_format(row_format)
        if assumption:
            content.add_assumption()
        if row_levels is not None:
            content.set_row_levels(row_levels)
        if row_formats is not None:
            content.set_row_formats(row_formats)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row

    def emit_ref_years_block(self, name, current_row, ref_range, row_format = OptimaFormats.GENERAL,
        assumption = None, row_levels = None, row_formats = None):
        content = make_ref_years_range(name, ref_range, self.data_start, self.data_end)
        content.set_row_format(row_format)
        if assumption:
            content.add_assumption()
        if row_levels is not None:
            content.set_row_levels(row_levels)
        if row_formats is not None:
            content.set_row_formats(row_formats)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row

    def generate_meta(self):
        self.current_sheet.set_column(2,2,15)
        self.current_sheet.set_column(3,3,40)
        self.current_sheet.set_column(6,6,12)
        self.current_sheet.set_column(7,7,16)
        self.current_sheet.set_column(8,8,16)
        self.current_sheet.set_column(9,9,12)
        current_row = 0

        pop_content = make_populations_range('Populations', self.pops)
        self.pop_range = TitledRange(self.current_sheet, current_row, pop_content) # we'll need it for references
        current_row = self.pop_range.emit(self.formats, rc_title_align = 'left')

        self.ref_pop_range = self.pop_range.param_refs()
        self.ref_females_range = filter_by_properties(self.ref_pop_range, self.pops, {'female':True})
        self.ref_males_range = filter_by_properties(self.ref_pop_range, self.pops, {'male':True})

    def generate_key(self):
        row_levels = ['high', 'best', 'low']
        current_row = 0

        current_row = self.emit_ref_years_block('HIV prevalence', current_row, self.pop_range, 
            row_format = OptimaFormats.DECIMAL_PERCENTAGE, assumption = True, row_levels = row_levels)

    def generate_popsize(self):
        row_levels = ['high', 'best', 'low']
        current_row = 0

        current_row = self.emit_ref_years_block('Population size', current_row, self.pop_range, 
            row_format = OptimaFormats.SCIENTIFIC, assumption = True, row_levels = row_levels)

    def generate_epi(self):
        current_row = 0

        for name in ['Percentage of people who die from non-HIV-related causes per year',
        'Prevalence of any ulcerative STIs', 'Tuberculosis prevalence']:
            current_row = self.emit_ref_years_block(name, current_row, self.pop_range, 
                row_format = OptimaFormats.DECIMAL_PERCENTAGE, assumption = True)

    def generate_opt(self):
        current_row = 0

        for name in ['Number of HIV tests per year', 'Number of HIV diagnoses per year', 
        'Modeled estimate of new HIV infections per year', 'Modeled estimate of HIV prevalence', 
        'Modeled estimate of number of PLHIV', 'Number of HIV-related deaths', 'Number of people initiating ART each year']:
            current_row = self.emit_years_block(name, current_row, ['Total'], row_format = OptimaFormats.NUMBER, assumption = True)


    def generate_txrx(self):
        current_row = 0
        current_row = self.emit_ref_years_block('Percentage of population tested for HIV in the last 12 months',current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_years_block('Probability of a person with CD4 <200 being tested per year',      current_row, ['Average'], row_format = OptimaFormats.GENERAL, assumption = True)
        current_row = self.emit_years_block('Number of people on treatment',                                    current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True)
        current_row = self.emit_ref_years_block('Percentage of people covered by pre-exposure prophylaxis',     current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_years_block('Number (or percentage) of women on PMTCT (Option B/B+)',           current_row, ['Total'], row_format = OptimaFormats.GENERAL, assumption = True)
        current_row = self.emit_years_block('Birth rate (births per woman per year)',                           current_row, self.ref_females_range, row_format = OptimaFormats.NUMBER, assumption = True)
        current_row = self.emit_years_block('Percentage of HIV-positive women who breastfeed',                  current_row, ['Total'], row_format = OptimaFormats.PERCENTAGE, assumption = True)        
        
    
    def generate_casc(self):
        current_row = 0
        current_row = self.emit_ref_years_block('Linkage to care from diagnosis within 1 month (%)',                                        current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_ref_years_block('Percentage of HIV-diagnosed people newly linked to care per year (%/year)',  current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_ref_years_block('Number of PLHIV who are in care',  current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_ref_years_block('Percentage of HIV-diagnosed people who are in care (%)',  current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_ref_years_block('Percentage of all PLHIV who are in care (%)',  current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_ref_years_block('Percentage of people who receive ART in the year who stop taking ART (%/year)',            current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_ref_years_block('Percentage of people in care who are lost to follow-up per year (%/year)',                 current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_ref_years_block('PLHIV lost to follow-up (%/year)',                                                         current_row, self.pop_range, row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_years_block('Biological failure rate (%/year)',                                                             current_row, ['Average'], row_format = OptimaFormats.PERCENTAGE, assumption = True)
        current_row = self.emit_years_block('Proportion of people on ART with viral suppression (%)',                                       current_row, ['Average'], row_format = OptimaFormats.PERCENTAGE, assumption = True)
            

    def generate_sex(self):
        current_row = 0
        names_formats_ranges = [('Average number of acts with regular partners per person per year', OptimaFormats.GENERAL, self.ref_pop_range),
        ('Average number of acts with casual partners per person per year', OptimaFormats.GENERAL, self.ref_pop_range),
        ('Average number of acts with commercial partners per person per year', OptimaFormats.GENERAL, self.ref_pop_range),
        ('Percentage of people who used a condom at last act with regular partners', OptimaFormats.PERCENTAGE, self.ref_pop_range),
        ('Percentage of people who used a condom at last act with casual partners', OptimaFormats.PERCENTAGE, self.ref_pop_range),
        ('Percentage of people who used a condom at last act with commercial partners', OptimaFormats.PERCENTAGE, self.ref_pop_range),
        ('Percentage of males who have been circumcised', OptimaFormats.PERCENTAGE, self.ref_males_range)]

        for (name, row_format, row_range) in names_formats_ranges:
            current_row = self.emit_years_block(name, current_row, row_range, row_format = row_format, assumption = True)

    def generate_inj(self):
        current_row = 0
        names_formats_ranges = [('Average number of injections per person per year', OptimaFormats.GENERAL, self.ref_pop_range),
        ('Average percentage of people who receptively shared a needle/syringe at last injection', OptimaFormats.PERCENTAGE, self.ref_pop_range),
        ('Number of people who inject drugs who are on opiate substitution therapy', OptimaFormats.GENERAL, ['Average'])]

        for (name, row_format, row_range) in names_formats_ranges:
            current_row = self.emit_years_block(name, current_row, row_range, row_format = row_format, assumption = True)

    def generate_ptrans(self):
        current_row = 0
        names = ['Interactions between regular partners', 'Interactions between casual partners',
        'Interactions between commercial partners', 'Interactions between people who inject drugs',
        'Risk-related population transitions (average number of years before movement)']

        for ind in range(len(self.pops)):
            self.current_sheet.set_column(2+ind,2+ind,12)
        for name in names:
            current_row = self.emit_matrix_block(name, current_row, self.ref_pop_range, self.ref_pop_range)

    def generate_const(self):
        self.current_sheet.set_column(1,1,40)
        current_row = 0

        names_rows_data_format = [
        ('Interaction-related transmissibility (% per act)',
            ['Insertive penile-vaginal intercourse', 
            'Receptive penile-vaginal intercourse', 
            'Insertive penile-anal intercourse', 
            'Receptive penile-anal intercourse',
            'Intravenous injection', 
            'Mother-to-child (breastfeeding)',
            'Mother-to-child (non-breastfeeding)'],
            [0.0004, 0.0008, 0.0138, 0.0011, 0.0080, 0.367, 0.205],
            [0.0001, 0.0006, 0.0102, 0.0004, 0.0063, 0.294, 0.14],
            [0.0014, 0.0011, 0.0186, 0.0028, 0.0240, 0.440, 0.270], 
            OptimaFormats.DECIMAL_PERCENTAGE),
        ('Relative disease-related transmissibility',
            ['Acute infection',
            'CD4(>500)',
            'CD4(500) to CD4(350-500)',
            'CD4(200-350)',
            'CD4(50-200)',
            'CD4(<50)'],
            [26.03,1,1,1,3.49,7.17], 
            [2,1,1,1,1.76,3.9], 
            [48.02,1,1,1,6.92,12.08], 
            OptimaFormats.NUMBER),
        ('Disease progression rate (% per year)',
            ['Acute to CD4(>500)',
            'CD4(500) to CD4(350-500)',
            'CD4(350-500) to CD4(200-350)',
            'CD4(200-350) to CD4(50-200)',
            'CD4(50-200) to CD4(<50)'], 
            [4.14, 1.05, 0.33, 0.27, 0.67], 
            [2.00, 0.86, 0.32, 0.25, 0.44], 
            [9.76, 1.61, 0.35, 0.29, 0.88],
            OptimaFormats.PERCENTAGE),
        ('Treatment recovery rate (% per year)',
            ['CD4(350-500) to CD4(>500)',
            'CD4(200-350) to CD4(350-500)',
            'CD4(50-200) to CD4(200-350)',
            'CD4(<50) to CD4(50-200)'],
            [0.45, 0.70, 0.47, 1.52], 
            [0.14, 0.29, 0.33, 1.06], 
            [0.93, 1.11, 0.72, 1.96], 
            OptimaFormats.PERCENTAGE),
        ('Death rate (% mortality per year)',
            ['Acute infection',
            'CD4(>500)',
            'CD4(350-500)',
            'CD4(200-350)',
            'CD4(50-200)',
            'CD4(<50)',
            'On treatment',
            'Tuberculosis cofactor'],
            [0.0036, 0.0036, 0.0058, 0.0088, 0.059, 0.3230, 0.2300, 2.17], 
            [0.0029, 0.0029, 0.0048, 0.0750, 0.0540, 0.2960, 0.1500, 1.27],
            [0.0044, 0.0044, 0.0071, 0.0101, 0.079, 0.4320, 0.3000, 3.71], 
            OptimaFormats.DECIMAL_PERCENTAGE),
        ('Changes in transmissibility (%)',
            ['Condom use',
            'Circumcision',
            'Diagnosis behavior change',
            'STI cofactor increase',
            'Opiate substitution therapy',
            'PMTCT',
            'Pre-exposure prophylaxis',
            'Unsuppressive ART',
            'Suppressive ART',
            'Probability of viral suppression on ART'],
            [0.95, 0.58, 0.54, 0., 2.65, 0.9, 0.73, 0.5, 0.92, 0.9], 
            [0.8, 0.47, 0.33, 0., 1.35, 0.82, 0.65, 0.3, 0.8, 0.8 ],
            [0.98, 0.67, 0.68, 0.68, 5.19, 0.93, 0.8, 0.8, 0.95, 0.95],
            OptimaFormats.PERCENTAGE),
        ('Disutility weights',
            ['Untreated HIV, acute',
            'Untreated HIV, CD4(>500)',
            'Untreated HIV, CD4(350-500)',
            'Untreated HIV, CD4(200-350)',
            'Untreated HIV, CD4(50-200)',
            'Untreated HIV, CD4(<50)',
            'Treated HIV'], 
            [0.146, 0.008, 0.020, 0.070, 0.265, 0.547, 0.053], 
            [0.096, 0.005, 0.013, 0.048, 0.114, 0.382, 0.034], 
            [0.205, 0.011, 0.029, 0.094, 0.474, 0.715, 0.079], 
            OptimaFormats.NUMBER)]

        for (name, row_names, best, low, high, format) in names_rows_data_format:
            current_row = self.emit_constants_block(name, current_row, row_names, best, low, high, format)

    def generate_instr(self):
        current_row = 0
        self.current_sheet.set_column('A:A',80)
        self.current_sheet.merge_range('A1:A3', 'O P T I M A', self.formats.formats['info_header'])
        current_row = 3
        current_row = self.formats.write_info_line(self.current_sheet, current_row)
        current_row = self.formats.write_info_block(self.current_sheet, current_row, row_height=65, text='Welcome to the Optima data entry spreadsheet. This is where all data for the model will be entered. Please ask someone from the Optima development team if you need help, or use the default contact (info@optimamodel.com).')
        current_row = self.formats.write_info_block(self.current_sheet, current_row, text='For further details please visit: http://optimamodel.com/file/indicator-guide')

    def create(self, path):
        if self.verbose >=1: 
            print("""Creating spreadsheet %s with parameters:
            npops = %s, data_start = %s, data_end = %s""" % \
            (path, self.npops, self.data_start, self.data_end))
        self.book = xlsxwriter.Workbook(path)
        self.formats = OptimaFormats(self.book)
        self.sheets = {}
        for name in self.sheet_names:
            self.sheets[name] = self.book.add_worksheet(self.sheet_names[name])
            self.current_sheet = self.sheets[name]
            getattr(self, "generate_%s" % name)() # this calls the corresponding generate function
        self.book.close()

class OptimaGraphTable:
    def __init__ (self, sheets, verbose = 2):
        self.verbose = verbose
        self.sheets = sheets

    def create(self, path):
        if self.verbose >=1:
            print("Creating graph table %s" % path)

        self.book = xlsxwriter.Workbook(path)
        self.formats = OptimaFormats(self.book)
        sheet_name = 'GRAPH DATA'

        k = 0
        for s in self.sheets:
            k += 1
            name = sheet_name + " " + str(k)
            sheet = self.book.add_worksheet(name)

            titles = [c['title'] for c in s["columns"]]
            max_row = max([len(c['data']) for c in s["columns"]])

            for i in range(len(s["columns"])):
                sheet.set_column(i,i,20)

            self.formats.write_block_name(sheet, s["name"], 0) #sheet name

            for i,title in enumerate(titles):
                self.formats.write_rowcol_name(sheet, 1, i, str(title))
            row =0
            while row<=max_row:
                for i,col in enumerate(s["columns"]):
                    if row<len(col['data']):
                        data = col['data'][row]
                    else:
                        data = None
                    self.formats.write_unlocked(sheet, row+2, i, data)
                row+=1
        self.book.close()
