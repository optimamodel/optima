"""
OptimaSpreadsheet and related classes
Created by: SSQ

Version: 2016jan18 by robyns
"""

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from utils import printv, isnumber
from numpy import isnan
from optima import __version__, odict, getdate, today, loadpartable

default_datastart = 2000
default_dataend = 2020

def makespreadsheet(filename=None, pops=None, datastart=default_datastart, dataend=default_dataend, data=None, verbose=2):
    """ Generate the Optima spreadsheet """

    # If population information isn't given...
    if pops is None:
        if data is None: pops=2 # No data provided either, so just make a 2 population spreadsheet
        else:
            pops = []
            npops = len(data['pops']['short'])
            for pop in range(npops):
                pops.append({
                         'short':    data['pops']['short'][pop],
                         'name':     data['pops']['long'][pop],
                         'male':     data['pops']['male'][pop],
                         'female':   data['pops']['female'][pop],
                         'age_from': data['pops']['age'][pop][0],
                         'age_to':   data['pops']['age'][pop][1]
                         })
        
    if isnumber(pops):
        npops = pops
        pops = [] # Create real pops list
        for p in range(npops):
            pops.append({'short_name':'Pop %i'%(p+1), 'name':'Population %i'%(p+1), 'male':True, 'female':True, 'age_from':0, 'age_to':99}) # Must match make_populations_range definitions
            
    # Ensure years are integers
    datastart, dataend = int(datastart), int(dataend)
    
    printv('Generating spreadsheet: pops=%i, datastart=%s, dataend=%s' % (len(pops), datastart, dataend), 1, verbose)

    book = OptimaSpreadsheet(filename, pops, datastart, dataend, data=data)
    book.create(filename)

    printv('  ...done making spreadsheet %s.' % filename, 2, verbose)
    return filename


def makeprogramspreadsheet(filename, pops, progs, datastart=default_datastart, dataend=default_dataend, verbose=2):
    """ Generate the Optima programs spreadsheet """

    # An integer argument is given: just create a pops dict using empty entries
    if isnumber(pops):
        npops = pops
        pops = [] # Create real pops list
        for p in range(npops):
            pops.append({'short_name':'Pop %i'%(p+1)}) # Must match make_populations_range definitions
    
    printv('Generating program spreadsheet: pops=%i, progs=%i, datastart=%s, dataend=%s' % (len(pops), len(progs), datastart, dataend), 1, verbose)

    book = OptimaProgramSpreadsheet(filename, pops, progs, datastart, dataend)
    book.create(filename)

    printv('  ...done making spreadsheet %s.' % filename, 2, verbose)
    return filename

def years_range(data_start, data_end):
    return [x for x in range(data_start, data_end+1)]

class OptimaContent:
    """ the content of the data ranges (row names, column names, optional data and assumptions) """
    def __init__(self, name, row_names, column_names, data=None, assumption_data=None):
        self.name = name
        self.row_names = row_names
        self.column_names = column_names
        self.data = data
        self.assumption = False
        self.row_levels = None
        self.row_format = OptimaFormats.GENERAL
        self.row_formats = None
        self.assumption_properties = {'title':None, 'connector':'OR', 'columns':['Assumption']}
        self.assumption_data = assumption_data
        self.rawpars = loadpartable()

    def set_row_format(self, row_format):
        self.row_format = row_format

    def has_data(self):
        return self.data != None

    def has_assumption_data(self):
        return self.assumption_data != None

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

""" It's not truly pythonic, they say, to have class methods """

def make_matrix_range(name, params, data=None):
    return OptimaContent(name, params, params, data=data)

def make_years_range(name, params, data_start, data_end, data=None):
    return OptimaContent(name, params, years_range(data_start, data_end), data=data)

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
            short_name = item.get('short', item_name)
            male = item.get('male', False)
            female = item.get('female', False)
            age_from = item.get('age_from',15)
            age_to = item.get('age_to',49)
        else: # backward compatibility :) might raise exception which is ok
            item_name = item
            short_name = item
            male = False
            female = False
            age_from = 15
            age_to = 49
        coded_params.append([short_name, item_name, male, female, age_from, age_to])
    return OptimaContent(name, row_names, column_names, coded_params)


def make_programs_range(name, popnames, items):
    """ 
    every programs item is a dictionary is expected to have the following fields:
    short_name, name, targetpops
    (2x str, 1x list of booleans)
    """
    column_names = ['Short name','Long name']+popnames
    row_names = range(1, len(items)+1)
    coded_params = []
    for item in items:
        if type(item) is dict:
            item_name = item['name']
            short_name = item['short']
            item_targetpops = [1 if popname in item['targetpops'] else 0 for popname in popnames]
        coded_params.append([short_name, item_name]+item_targetpops)
    return OptimaContent(name=name, row_names=row_names, column_names=column_names, data=coded_params)


def make_constant_range(name, row_names, best_data, low_data, high_data):
    column_names = ['best', 'low', 'high']
    range_data = [[best, low, high] for (best, low, high) in zip(best_data, low_data, high_data)]
    return OptimaContent(name, row_names, column_names, range_data)

def make_ref_years_range(name, ref_range, data_start, data_end, data=None):
    params = ref_range.param_refs()
    return make_years_range(name, params, data_start, data_end, data=data)

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

def nan2blank(thesedata):
    ''' Convert a nan entry to a blank entry'''
    return list(map(lambda val: '' if isnan(val) else val, thesedata))

class OptimaFormats:
    """ the formats used in the spreadsheet """
    darkgray = '#413839'
    originalblue = '#18C1FF'
    optionalorange = '#FFA500'
    hotpink = '#FFC0CB'
    BG_COLOR = originalblue
    OPT_COLOR = optionalorange
    BORDER_COLOR = 'white'

    PERCENTAGE = 'percentage'
    DECIMAL = 'decimal'
    SCIENTIFIC = 'scientific'
    NUMBER = 'number'
    GENERAL = 'general'
    OPTIONAL = 'optional'

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
        self.formats['unlocked']     = self.book.add_format({'locked':0, 'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['percentage']   = self.book.add_format({'locked':0, 'num_format':0x09, 'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['decimal']      = self.book.add_format({'locked':0, 'num_format':0x0a, 'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['scientific']   = self.book.add_format({'locked':0, 'num_format':0x0b, 'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['number']       = self.book.add_format({'locked':0, 'num_format':0x04, 'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['general']      = self.book.add_format({'locked':0, 'num_format':0x00, 'bg_color':OptimaFormats.BG_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['optional']     = self.book.add_format({'locked':0, 'num_format':0x00, 'bg_color':OptimaFormats.OPT_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['info_header']  = self.book.add_format({'align':'center','valign':'vcenter', 'color':'#D5AA1D','fg_color':'#0E0655', 'font_size':20})
        self.formats['grey']         = self.book.add_format({'fg_color':'#EEEEEE', 'text_wrap':True})
        self.formats['info_url']     = self.book.add_format({'fg_color':'#EEEEEE', 'text_wrap':True, 'color':'blue','align':'center'})
        self.formats['grey_bold']    = self.book.add_format({'fg_color':'#EEEEEE','bold':True})
        self.formats['merge_format'] = self.book.add_format({'bold': 1,'align': 'center','text_wrap':True})


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

        if self.content.assumption and  self.first_row==0 and self.content.assumption_properties['title'] is not None:
            formats.write_rowcol_name(self.sheet, self.first_row, self.data_range.last_col+2, self.content.assumption_properties['title'])

        #headers
        for i, name in enumerate(self.content.column_names):
            formats.write_rowcol_name(self.sheet, self.first_row+1, self.data_range.first_col+i,name, rc_title_align)
        if self.content.assumption:
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
                for j, item in enumerate(self.content.data[i]):
                    formats.write_unlocked(self.sheet, current_row, self.data_range.first_col+j, item, row_format)
            else:
                for j in range(self.data_range.num_cols):
                    formats.write_empty_unlocked(self.sheet, current_row, self.data_range.first_col+j, row_format)
            #emit assumption
            if self.content.assumption:
                formats.write_option(self.sheet, current_row, self.data_range.last_col+1, \
                    name = self.content.assumption_properties['connector'])
                for index, col_name in enumerate(self.content.assumption_properties['columns']):
                    if self.content.has_assumption_data():
                        formats.write_unlocked(self.sheet, current_row, self.data_range.last_col+2+index, self.content.assumption_data[i], row_format)
                    else:
                        formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col+2+index, row_format)
            current_row+=1
            if num_levels > 1 and ((i+1) % num_levels)==0: # shift between the blocks
                current_row +=1
        #done! return the new current_row plus spacing
        return current_row + TitledRange.ROW_INTERVAL # for spacing

    def param_refs(self, column_number = 0):
        return self.data_range.param_refs(self.sheet.get_name(), column_number)


class OptimaSpreadsheet:
    def __init__(self, name, pops, data_start = default_datastart, data_end = default_dataend, data = None, verbose = 0):
        self.sheet_names = odict([
            ('instr', 'Instructions'),
            ('meta','Populations'),
            ('popsize', 'Population size'),
            ('key', 'HIV prevalence'),
            ('epi', 'Other epidemiology'),
            ('txrx', 'Testing & treatment'),
            ('opt', 'Optional indicators'),
            ('casc', 'Cascade'),
            ('sex', 'Sexual behavior'),
            ('inj', 'Injecting behavior'),
            ('ptrans', 'Partnerships & transitions'),
            ('const', 'Constants')])
        self.name = name
        self.pops = pops
        self.data_start = data_start
        self.data_end = data_end
        self.data = data
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
        content.assumption = assumption
        if assumption_properties:
            content.set_assumption_properties(assumption_properties)
        if row_levels is not None:
            content.set_row_levels(row_levels)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row


    def emit_matrix_block(self, name, current_row, row_names, column_names=None, data=None):
        if column_names is None:
            column_names = row_names
        content = OptimaContent(name, row_names, column_names, data=data)
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

    def emit_years_block(self, name, current_row, row_names, row_format=OptimaFormats.GENERAL,
        assumption=False, row_levels=None, row_formats=None, data=None, assumption_data=None):
        content = make_years_range(name, row_names, self.data_start, self.data_end, data=data)
        content.set_row_format(row_format)
        content.assumption = assumption
        content.assumption_data = assumption_data
        if row_levels is not None:
            content.set_row_levels(row_levels)
        if row_formats is not None:
            content.set_row_formats(row_formats)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row

    def emit_ref_years_block(self, name, current_row, ref_range, row_format = OptimaFormats.GENERAL,
        assumption = None, row_levels = None, row_formats = None, data = None, assumption_data=None):
        content = make_ref_years_range(name, ref_range, self.data_start, self.data_end, data=data)
        content.set_row_format(row_format)
        content.assumption = assumption
        content.assumption_data = assumption_data
        if row_levels is not None:
            content.set_row_levels(row_levels)
        if row_formats is not None:
            content.set_row_formats(row_formats)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row
        
    def formatkeydata(self, data):
        '''
        Return key data in a format that can be written to spreadsheet
        Data in projects is formatted as [[best-pop1, best-pop2,... ], [low-pop1, low-pop2,... ], [high-pop1, high-pop2,... ]]
        This method reformats the key data so it's arranged as [high-pop1, best-pop1, low-pop1, high-pop1, best-pop2, low-pop2, ... ]
        '''
        newdata = []
        assumption = []
        npops = len(data[0]) 
        npts = self.data_end-self.data_start+1
        for pop in range(npops):
            for est in [2,0,1]: # Looping though best/low/high
                if len(data[est][pop])==1: # It's an assumption
                    newdata.append(['']*npts)
                    assumption.append(data[est][pop])
                elif len(data[est][pop])==npts: # It's data
                    newdata.append(nan2blank(data[est][pop]))
                    assumption.append('')
        return {'data':newdata,'assumption_data':assumption}

    def formattimedata(self, data):
        ''' Return standard time data in a format that can be written to spreadsheet'''
        newdata = []
        assumption = []
        npops = len(data) # Data in projects is formatted as [pop1, pop2, ... ]
        npts = self.data_end-self.data_start+1
        for pop in range(npops):
            if len(data[pop])==1: # It's an assumption
                newdata.append(['']*npts)
                assumption.append(nan2blank(data[pop])[0])
            elif len(data[pop])==npts: # It's data
                newdata.append(nan2blank(data[pop]))                
                assumption.append('')
        return {'data':newdata,'assumption_data':assumption}

    def getdata(self, name):
        ''' Get the short name of indicators in the data sheet'''
        for par in self.rawpars:
            if par['dataname']==name:
                shortname = par['dataname']
#        return [par['datashort']  if ][0]
        return self.data.get(shortname)

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
        self.ref_child_range = filter_by_properties(self.ref_pop_range, self.pops, {'age_from':0})

    def generate_key(self, data=None, assumption_data=None):
        row_levels = ['high', 'best', 'low']
        current_row = 0
        name = 'HIV prevalence'
        if self.data is not None:
            data = self.formatkeydata(self.data.get('hivprev'))['data']
            assumption_data = self.formatkeydata(self.data.get('hivprev'))['assumption_data']
        current_row = self.emit_ref_years_block(name, current_row, self.pop_range, 
            row_format=OptimaFormats.DECIMAL, assumption=True, row_levels=row_levels, data=data, assumption_data=assumption_data)

    def generate_popsize(self, data=None, assumption_data=None):
        row_levels = ['high', 'best', 'low']
        current_row = 0
        name = 'Population size'
        if self.data is not None:
            data = self.formatkeydata(self.getdata(name))['data']
            assumption_data = self.formatkeydata(self.getdata(name))['assumption_data']
        current_row = self.emit_ref_years_block(name, current_row, self.pop_range, 
                            row_format=OptimaFormats.GENERAL, assumption=True, row_levels=row_levels, data=data, assumption_data=assumption_data)
            
    def generate_epi(self, data=None, assumption_data=None):
        current_row = 0

        for name in ['Percentage of people who die from non-HIV-related causes per year',
        'Prevalence of any ulcerative STIs', 'Tuberculosis prevalence']:
            if self.data is not None:
                data = self.formattimedata(self.getdata(name))['data']
                assumption_data = self.formattimedata(self.getdata(name))['assumption_data']
                
            current_row = self.emit_ref_years_block(name, current_row, self.pop_range, 
                row_format=OptimaFormats.DECIMAL, assumption=True, data=data, assumption_data=assumption_data)

    def generate_txrx(self, data=None, assumption_data=None):
        current_row = 0
        methods_names_formats_ranges = [
        ('emit_ref_years_block',    'Percentage of population tested for HIV in the last 12 months',    OptimaFormats.PERCENTAGE,   self.pop_range),
        ('emit_years_block',        'Probability of a person with CD4 <200 being tested per year',      OptimaFormats.GENERAL,      ['Average']),
        ('emit_years_block',        'Number of people on treatment',                                    OptimaFormats.GENERAL,      ['Total']),
        ('emit_years_block',        'Unit cost of treatment',                                           OptimaFormats.GENERAL,      ['Total']),
        ('emit_ref_years_block',    'Percentage of people covered by pre-exposure prophylaxis',         OptimaFormats.PERCENTAGE,   self.pop_range),
        ('emit_years_block',        'Number of women on PMTCT (Option B/B+)',                           OptimaFormats.GENERAL,      ['Total']),
        ('emit_years_block',        'Birth rate (births per woman per year)',                           OptimaFormats.NUMBER,       self.ref_females_range),
        ('emit_years_block',        'Percentage of HIV-positive women who breastfeed',                  OptimaFormats.PERCENTAGE,   ['Total']),
        ]
        for (method, name, row_format, row_range) in methods_names_formats_ranges:
            if self.data is not None:
                data = self.formattimedata(self.getdata(name))['data']
                assumption_data = self.formattimedata(self.getdata(name))['assumption_data']
            current_row = getattr(self, method)(name, current_row, row_range, row_format=row_format, assumption=True, data=data, assumption_data=assumption_data)

    def generate_opt(self, data=None, assumption_data=None):
        current_row = 0
        names_formats_ranges = [
        ('Number of HIV tests per year',                    OptimaFormats.NUMBER,       ['Total']),
        ('Number of HIV diagnoses per year',                OptimaFormats.NUMBER,       ['Total']),
        ('Modeled estimate of new HIV infections per year', OptimaFormats.NUMBER,       ['Total']),
        ('Modeled estimate of HIV prevalence',              OptimaFormats.NUMBER,       ['Total']),
        ('Modeled estimate of number of PLHIV',             OptimaFormats.NUMBER,       ['Total']),
        ('Number of HIV-related deaths',                    OptimaFormats.NUMBER,       ['Total']),
        ('Number of people initiating ART each year',       OptimaFormats.NUMBER,       ['Total']),
        ('PLHIV aware of their status (%)',                 OptimaFormats.PERCENTAGE,   ['Average']),
        ('Diagnosed PLHIV in care (%)',                     OptimaFormats.PERCENTAGE,   ['Average']),
        ('PLHIV in care on treatment (%)',                  OptimaFormats.PERCENTAGE,   ['Average']),
        ('Pregnant women on PMTCT (%)',                     OptimaFormats.PERCENTAGE,   ['Average']),
        ('People on ART with viral suppression (%)',        OptimaFormats.PERCENTAGE,   ['Average'])
        ]
        
        for (name, row_format, row_range) in names_formats_ranges:
            if self.data is not None:
                data = self.formattimedata(self.getdata(name))['data']
                assumption_data = self.formattimedata(self.getdata(name))['assumption_data']
            current_row = self.emit_years_block(name, current_row, row_range, row_format=row_format, assumption=True, data=data, assumption_data=assumption_data)
    
    def generate_casc(self, data=None, assumption_data=None):
        current_row = 0
        methods_names_formats_ranges = [
        ('emit_ref_years_block',    'Average time taken to be linked to care (years)',                  OptimaFormats.NUMBER,       self.pop_range),
        ('emit_years_block',        'Average time taken to be linked to care for people with CD4<200 (years)',     OptimaFormats.PERCENTAGE,           ['Average']),
        ('emit_ref_years_block',    'Percentage of people in care who are lost to follow-up per year (%/year)',    OptimaFormats.PERCENTAGE,   self.pop_range),
        ('emit_years_block',        'Percentage of people with CD4<200 lost to follow-up (%/year)',     OptimaFormats.PERCENTAGE,           ['Average']),
        ('emit_years_block',        'Viral load monitoring (number/year)',                              OptimaFormats.NUMBER,           ['Average']),
        ]
        for (method, name, row_format, row_range) in methods_names_formats_ranges:
            if self.data is not None:
                data = self.formattimedata(self.getdata(name))['data']
                assumption_data = self.formattimedata(self.getdata(name))['assumption_data']
            current_row = getattr(self, method)(name, current_row, row_range, row_format=row_format, assumption=True, data=data, assumption_data=assumption_data)

    def generate_sex(self, data=None, assumption_data=None):
        current_row = 0
        names_formats_ranges = [
        ('Average number of acts with regular partners per person per year', OptimaFormats.GENERAL, self.ref_pop_range),
        ('Average number of acts with casual partners per person per year', OptimaFormats.GENERAL, self.ref_pop_range),
        ('Average number of acts with commercial partners per person per year', OptimaFormats.GENERAL, self.ref_pop_range),
        ('Percentage of people who used a condom at last act with regular partners', OptimaFormats.PERCENTAGE, self.ref_pop_range),
        ('Percentage of people who used a condom at last act with casual partners', OptimaFormats.PERCENTAGE, self.ref_pop_range),
        ('Percentage of people who used a condom at last act with commercial partners', OptimaFormats.PERCENTAGE, self.ref_pop_range),
        ('Percentage of males who have been circumcised', OptimaFormats.PERCENTAGE, self.ref_males_range)]

        for (name, row_format, row_range) in names_formats_ranges:
            if self.data is not None:
                data = self.formattimedata(self.getdata(name))['data']
                assumption_data = self.formattimedata(self.getdata(name))['assumption_data']
            current_row = self.emit_years_block(name, current_row, row_range, row_format = row_format, assumption = True, data=data, assumption_data=assumption_data)

    def generate_inj(self, data=None, assumption_data=None):
        current_row = 0
        names_formats_ranges = [
        ('Average number of injections per person per year', OptimaFormats.GENERAL, self.ref_pop_range),
        ('Average percentage of people who receptively shared a needle/syringe at last injection', OptimaFormats.PERCENTAGE, self.ref_pop_range),
        ('Number of people who inject drugs who are on opiate substitution therapy', OptimaFormats.GENERAL, ['Average'])]

        for (name, row_format, row_range) in names_formats_ranges:
            if self.data is not None:
                data = self.formattimedata(self.getdata(name))['data']
                assumption_data = self.formattimedata(self.getdata(name))['assumption_data']
            current_row = self.emit_years_block(name, current_row, row_range, row_format=row_format, assumption=True, data=data, assumption_data=assumption_data)

    def generate_ptrans(self, data=None):
        current_row = 0
        names = ['Interactions between regular partners', 'Interactions between casual partners',
        'Interactions between commercial partners', 'Interactions between people who inject drugs',
        'Births', 'Aging', 'Risk-related population transitions (average number of years before movement)']

        for ind in range(len(self.pops)):
            self.current_sheet.set_column(2+ind,2+ind,12)
        for name in names:
            if self.data is not None: data = self.getdata(name)
            if name=='Births': current_row = self.emit_matrix_block(name, current_row, self.ref_females_range, self.ref_pop_range, data=data)
            else: current_row = self.emit_matrix_block(name, current_row, self.ref_pop_range, self.ref_pop_range, data=data)

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
            [0.0004, 0.0008, 0.0011, 0.0138, 0.0080, 0.367, 0.205],
            [0.0001, 0.0006, 0.0004, 0.0102, 0.0063, 0.294, 0.14],
            [0.0014, 0.0011, 0.0028, 0.0186, 0.0240, 0.440, 0.270], 
            OptimaFormats.DECIMAL),
        ('Relative disease-related transmissibility',
            ['Acute infection',
            'CD4(>500)',
            'CD4(500) to CD4(350-500)',
            'CD4(200-350)',
            'CD4(50-200)',
            'CD4(<50)'],
            [5.6,1,1,1,3.49,7.17], 
            [3.3,1,1,1,1.76,3.9], 
            [9.1,1,1,1,6.92,12.08], 
            OptimaFormats.NUMBER),
        ('Disease progression (average years to move)',
            ['Acute to CD4(>500)',
            'CD4(500) to CD4(350-500)',
            'CD4(350-500) to CD4(200-350)',
            'CD4(200-350) to CD4(50-200)',
            'CD4(50-200) to CD4(<50)'], 
            [0.24, 0.95, 3.00, 3.74, 1.50], 
            [0.10, 0.62, 2.83, 3.48, 1.13], 
            [0.50, 1.16, 3.16, 4.00, 2.25],
            OptimaFormats.NUMBER),
        ('Treatment recovery due to suppressive ART (average years to move)',
            ['CD4(350-500) to CD4(>500)',
            'CD4(200-350) to CD4(350-500)',
            'CD4(50-200) to CD4(200-350)',
            'CD4(<50) to CD4(50-200)',
            'Time after initiating ART to achieve viral suppression (years)',
            'Number of VL tests recommended per person per year'],
            [2.20, 1.42, 2.14, 0.66, 0.20, 2.0], 
            [1.07, 0.90, 1.39, 0.51, 0.10, 1.5], 
            [7.28, 3.42, 3.58, 0.94, 0.30, 2.5], 
            OptimaFormats.NUMBER),     
        ('CD4 change due to non-suppressive ART (%/year)',
            ['CD4(500) to CD4(350-500)',
             'CD4(350-500) to CD4(>500)',
             'CD4(350-500) to CD4(200-350)',
             'CD4(200-350) to CD4(350-500)',
             'CD4(200-350) to CD4(50-200)',
             'CD4(50-200) to CD4(200-350)',
             'CD4(50-200) to CD4(<50)',
             'CD4(<50) to CD4(50-200)',
             'Treatment failure rate'],
            [0.026, 0.150, 0.100, 0.053, 0.162, 0.117, 0.090, 0.111, 0.16],
            [0.005, 0.038, 0.022, 0.008, 0.050, 0.032, 0.019, 0.047, 0.05],
            [0.275, 0.885, 0.870, 0.827, 0.869, 0.686, 0.723, 0.563, 0.26],
            OptimaFormats.PERCENTAGE),
        ('Death rate (% mortality per year)',
            ['Acute infection',
            'CD4(>500)',
            'CD4(350-500)',
            'CD4(200-350)',
            'CD4(50-200)',
            'CD4(<50)',
            'Relative death rate on suppressive ART',
            'Relative death rate on non-suppressive ART',
            'Tuberculosis cofactor'],
            [0.0036, 0.0036, 0.0058, 0.0088, 0.059, 0.3230, 0.2300, 0.4878, 2.17], 
            [0.0029, 0.0029, 0.0048, 0.0075, 0.0540, 0.2960, 0.1500, 0.2835, 1.27],
            [0.0044, 0.0044, 0.0071, 0.0101, 0.079, 0.4320, 0.3000, 0.8417, 3.71], 
            OptimaFormats.DECIMAL),
        ('Changes in transmissibility (%)',
            ['Condom use',
            'Circumcision',
            'Diagnosis behavior change',
            'STI cofactor increase',
            'Opiate substitution therapy',
            'PMTCT',
            'Pre-exposure prophylaxis',
            'Unsuppressive ART',
            'Suppressive ART'],
            [0.95, 0.58, 0.0, 2.65, 0.54, 0.9, 0.73, 0.5, 0.92],
            [0.8, 0.47, 0.0, 1.35, 0.33, 0.82, 0.65, 0.3, 0.8],
            [0.98, 0.67, 0.68, 5.19, 0.68, 0.93, 0.8, 0.8, 0.95],
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
            OptimaFormats.NUMBER),
        ]


        for (name, row_names, best, low, high, format) in names_rows_data_format:
            current_row = self.emit_constants_block(name, current_row, row_names, best, low, high, format)

    def generate_instr(self):
        current_row = 0
        self.current_sheet.set_column('A:A',80)
        self.current_sheet.merge_range('A1:A3', 'O P T I M A   2 . 0', self.formats.formats['info_header'])
        current_row = 3
        current_row = self.formats.write_info_line(self.current_sheet, current_row)
        current_row = self.formats.write_info_block(self.current_sheet, current_row, row_height=65, text='Welcome to the Optima 2.0 data entry spreadsheet. This is where all data for the model will be entered. Please ask someone from the Optima development team if you need help, or use the default contact (info@optimamodel.com).')
        current_row = self.formats.write_info_block(self.current_sheet, current_row, text='For further details please visit: http://optimamodel.com/file/indicator-guide')
        current_row = self.formats.write_info_block(self.current_sheet, current_row, text='Spreadsheet created with Optima version %s' % __version__)
        current_row = self.formats.write_info_block(self.current_sheet, current_row, text='Date created: %s' % getdate(today()))

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





class OptimaProgramSpreadsheet:
    def __init__(self, name, pops, progs, data_start = default_datastart, data_end = default_dataend, verbose = 0):
        self.sheet_names = odict([
            ('instr', 'Instructions'),
            ('targeting','Populations & programs'),
            ('costcovdata', 'Program data'),
            ])
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
        self.prog_range = None
        self.ref_pop_range = None
        self.years_range = years_range(self.data_start, self.data_end)

        self.npops = len(pops)
        self.nprogs = len(progs)

    def generate_targeting(self):
        self.current_sheet.set_column(2,2,15)
        self.current_sheet.set_column(3,3,40)
        self.current_sheet.set_column(6,6,12)
        self.current_sheet.set_column(7,7,16)
        self.current_sheet.set_column(8,8,16)
        self.current_sheet.set_column(9,9,12)
        current_row = 0

        targeting_content = make_programs_range('Populations & programs', self.pops, self.progs)
        self.prog_range = TitledRange(sheet=self.current_sheet, first_row=current_row, content=targeting_content)
        current_row = self.prog_range.emit(self.formats, rc_title_align = 'left')

        self.ref_prog_range = self.prog_range


    def generate_instr(self):
        current_row = 0
        self.current_sheet.set_column('A:A',80)
        self.current_sheet.merge_range('A1:A3', 'O P T I M A   2 . 0', self.formats.formats['info_header'])
        current_row = 3
        current_row = self.formats.write_info_line(self.current_sheet, current_row)
        current_row = self.formats.write_info_block(self.current_sheet, current_row, row_height=65, text='Welcome to the Optima 2.0 program data entry spreadsheet. This is where all program data will be entered. Please ask someone from the Optima development team if you need help, or use the default contact (info@optimamodel.com).')
        current_row = self.formats.write_info_block(self.current_sheet, current_row, text='For further details please visit: http://optimamodel.com/file/indicator-guide')


    def emit_years_block(self, name, current_row, row_names, row_format = OptimaFormats.GENERAL,
        assumption = False, row_levels = None, row_formats = None):
        content = make_years_range(name, row_names, self.data_start, self.data_end)
        content.set_row_format(row_format)
        content.assumption = assumption
        if row_levels is not None:
            content.set_row_levels(row_levels)
        if row_formats is not None:
            content.set_row_formats(row_formats)
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row


    def generate_costcovdata(self):
        row_levels = ['Total spend', 'Unit cost: best', 'Unit cost: low', 'Unit cost: high', 'Coverage', 'Saturation: best', 'Saturation: low', 'Saturation: high']
        self.current_sheet.set_column('C:C',20)
        current_row = 0
        current_row = self.emit_years_block(name='Cost & coverage', current_row=current_row, row_names=self.ref_prog_range.param_refs(), row_formats = [OptimaFormats.SCIENTIFIC,OptimaFormats.GENERAL,OptimaFormats.OPTIONAL,OptimaFormats.OPTIONAL,OptimaFormats.OPTIONAL,OptimaFormats.OPTIONAL,OptimaFormats.OPTIONAL,OptimaFormats.OPTIONAL], assumption = True, row_levels = row_levels)


    def create(self, path):
        if self.verbose >=1: 
            print("""Creating program spreadsheet %s with parameters:
            npops = %s, nprogs = %s, data_start = %s, data_end = %s""" % \
            (path, self.npops, self.nprogs, self.data_start, self.data_end))
        self.book = xlsxwriter.Workbook(path)
        self.formats = OptimaFormats(self.book)
        self.sheets = {}
        for name in self.sheet_names:
            self.sheets[name] = self.book.add_worksheet(self.sheet_names[name])
            self.current_sheet = self.sheets[name]
            getattr(self, "generate_%s" % name)() # this calls the corresponding generate function
        self.book.close()
