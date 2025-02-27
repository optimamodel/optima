"""
Functions and classes for generating Excel spreadsheets.

Originally created by Anna Nachesa + StarterSquad

Version: 2017feb10
"""

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from numpy import isnan, nan, pad
from optima import printv, isnumber, supported_versions, versions_different_databook, compareversions, odict, getdate, today, loaddatapars, Settings, promotetolist, OptimaException


settings = Settings()
default_datastart = settings.start
default_dataend    = settings.dataend

__all__ = [
    'makespreadsheet',
    'makeprogramspreadsheet',
    'default_datastart',
    'default_dataend',
    'compatibledatabookversion',
]

def compatibledatabookversion(projectversions):
    def versiontoint(version):
        split = version.split('.')
        return 1000000000000 * int(split[0]) + 1000000 * int(split[1]) + int(split[2])

    thisprojectversions = promotetolist(projectversions)
    databookversions = [None] * len(thisprojectversions)
    for i, projectversion in enumerate(thisprojectversions):
        for databookversion in sorted(versions_different_databook, key=versiontoint):
            if compareversions(projectversion, databookversion) >= 0:
                databookversions[i] = databookversion
    return databookversions[0] if type(projectversions) == str else databookversions


def makespreadsheet(filename=None, pops=None, datastart=None, dataend=None, data=None, verbose=2, version=None):
    """
    Generate the Optima spreadsheet. pops can be supplied as a number of populations, 
    or as a list of dictionaries with keys 'short', 'name', 'male', 'female', 'age_from', 'age_to'.
    """

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
            pops.append({'short':'Pop %i'%(p+1), 'name':'Population %i'%(p+1), 'male':True, 'female':True, 'age_from':0, 'age_to':99}) # Must match make_populations_range definitions
            
    # Ensure years are integers
    if datastart is None: datastart = default_datastart
    if dataend is None:   dataend   = default_dataend
    datastart, dataend = int(datastart), int(dataend)
    
    printv('Generating spreadsheet: pops=%i, datastart=%s, dataend=%s' % (len(pops), datastart, dataend), 1, verbose)

    book = OptimaSpreadsheet(filename, pops, datastart, dataend, data=data, verbose=verbose, version=version)
    book.create(filename)

    printv('  ...done making spreadsheet %s.' % filename, 2, verbose)
    return filename


def makeprogramspreadsheet(filename, pops, progs, datastart=None, dataend=None, verbose=2):
    """ Generate the Optima programs spreadsheet """

    # An integer argument is given: just create a pops dict using empty entries
    if isnumber(pops):
        npops = pops
        pops = [] # Create real pops list
        for p in range(npops):
            pops.append({'short_name':'Pop %i'%(p+1)}) # Must match make_populations_range definitions
    
    # Ensure years are integers
    if datastart is None: datastart = default_datastart
    if dataend is None:   dataend   = default_dataend
    datastart, dataend = int(datastart), int(dataend)
    
    
    printv('Generating program spreadsheet: pops=%i, progs=%i, datastart=%s, dataend=%s' % (len(pops), len(progs), datastart, dataend), 1, verbose)

    book = OptimaProgramSpreadsheet(filename, pops, progs, datastart, dataend)
    book.create(filename)

    printv('  ...done making spreadsheet %s.' % filename, 2, verbose)
    return filename


class OptimaContent(object):
    """ the content of the data ranges (row names, column names, optional data and assumptions) """
    def __init__(self, name=None, row_names=None, column_names=None, data=None, assumption_data=None, assumption=True):
        self.name = name
        self.row_names = row_names
        self.column_names = column_names
        self.data = data
        self.assumption = assumption
        self.row_levels = None
        self.row_format = OptimaFormats.GENERAL
        self.row_formats = None
        self.assumption_properties = {'title':None, 'connector':'OR', 'columns':['Assumption']}
        self.assumption_data = assumption_data

    def get_row_names(self):
        if not self.row_levels is not None:
            return [[name] for name in self.row_names]
        else:
            return [[name, level] for name in self.row_names for level in self.row_levels]

    def get_row_formats(self): #assume that the number of row_formats is same as the number of row_levels
        if not self.row_levels is not None:
            return [self.row_format for name in self.row_names]
        else:
            if self.row_formats is not None:
                return [row_format for name in self.row_names for row_format in self.row_formats]
            else:
                return [self.row_format for name in self.row_names for level in self.row_levels]

""" It's not truly pythonic, they say, to have class methods """ # <- historic comment from Anna Nachesa

def make_years_range(name=None, row_names=None, ref_range=None, data_start=None, data_end=None, data=None):
    if ref_range is not None:
        row_names = ref_range.param_refs()
    output = OptimaContent(name=name, row_names=row_names, column_names=range(int(data_start), int(data_end+1)), data=data)
    return output

def make_populations_range(name=None, items=None):
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
    return OptimaContent(name=name, row_names=row_names, column_names=column_names, data=coded_params, assumption=False)


def make_programs_range(name=None, popnames=None, items=None):
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
    return OptimaContent(name=name, row_names=row_names, column_names=column_names, data=range_data)


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

def zero2blank(thesedata):
    ''' Convert a nan entry to a blank entry'''
    return list(map(lambda val: '' if val==0 else val, thesedata))

def getyearindspads(datayears, startyear, endyear):
    padstartyears = 0
    if startyear < datayears[0]:
        startind = 0
        padstartyears = round(datayears[0] - startyear)
    elif startyear not in datayears:
        raise OptimaException(f'Cannot start spreadsheet at year {startyear} because the data has years {datayears}')
    else:
        startind = list(datayears).index(startyear)

    padendyears = 0
    if endyear > datayears[-1]:
        endind = len(datayears)
        padendyears = round(endyear - datayears[-1])
    elif endyear not in datayears:
        raise OptimaException(f'Cannot stop spreadsheet at year {endyear} because the data has years {datayears}')
    else:
        endind = list(datayears).index(endyear)

    return startind, padstartyears, endind, padendyears

def padunpad(name, datarow, datayears, startyear, endyear):
    startind, padstartyears, endind, padendyears = getyearindspads(datayears, startyear, endyear)

    if not all(isnan(datarow[:startind])):
        raise OptimaException(f'Cannot start spreadsheet at year {startyear} because there is non-empty data in parameter {name} before then: {list(zip(datayears[:startind],datarow[:startind]))}')
    if not all(isnan(datarow[endind+1:])):
        raise OptimaException(f'Cannot stop spreadsheet at year {endyear} because there is non-empty data in parameter {name} after then: {list(zip(datayears[endind+1:],datarow[endind+1:]))}')

    newdatarow = pad(datarow[startind:endind+1], (padstartyears, padendyears), mode='constant', constant_values=(nan, nan))

    if len(newdatarow) != round(endyear - startyear) + 1:
        raise OptimaException(f'Could not properly pad parameter, had length {len(newdatarow)} expected {round(startyear - endyear) + 1}. input: {dict(name=name, datarow=datarow, datayears=datayears, startyear=startyear, endyear=endyear)}')

    return newdatarow



class OptimaFormats:
    """ the formats used in the spreadsheet """
    darkgray = '#413839'
    originalblue = '#18C1FF'
    optionalorange = '#FFA500'
    BG_COLOR = originalblue
    OPT_COLOR = optionalorange
    BORDER_COLOR = 'white'

    PERCENTAGE = 'percentage'
    RATE = 'rate'
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
        self.formats['unlocked']     = self.book.add_format({'locked':0,                    'bg_color':OptimaFormats.BG_COLOR, 'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['percentage']   = self.book.add_format({'locked':0, 'num_format':0x09, 'bg_color':OptimaFormats.BG_COLOR, 'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['rate']         = self.book.add_format({'locked':0, 'num_format':0x09, 'bg_color':OptimaFormats.BG_COLOR, 'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['decimal']      = self.book.add_format({'locked':0, 'num_format':0x0a, 'bg_color':OptimaFormats.BG_COLOR, 'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['scientific']   = self.book.add_format({'locked':0, 'num_format':0x0b, 'bg_color':OptimaFormats.BG_COLOR, 'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['number']       = self.book.add_format({'locked':0, 'num_format':0x04, 'bg_color':OptimaFormats.BG_COLOR, 'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['general']      = self.book.add_format({'locked':0, 'num_format':0x00, 'bg_color':OptimaFormats.BG_COLOR, 'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['optional']     = self.book.add_format({'locked':0, 'num_format':0x00, 'bg_color':OptimaFormats.OPT_COLOR,'border':1, 'border_color':OptimaFormats.BORDER_COLOR})
        self.formats['info_header']  = self.book.add_format({'align':'center','valign':'vcenter', 'font_color':'#D5AA1D','fg_color':'#0E0655', 'font_size':20})
        self.formats['grey']         = self.book.add_format({'fg_color':'#EEEEEE', 'text_wrap':True})
        self.formats['orange']       = self.book.add_format({'fg_color':'#FFC65E', 'text_wrap':True})
        self.formats['info_url']     = self.book.add_format({'fg_color':'#EEEEEE', 'text_wrap':True, 'font_color':'blue','align':'center'})
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

    def writeline(self, sheet, row, row_format='grey'):
        sheet.write_blank(row, 0, None, self.formats[row_format])
        return row+1

    def writeblock(self, sheet, row, text, row_format = 'grey', row_height = None, add_line = True):
        if row_height:
            sheet.set_row(row, row_height)
        sheet.write(row, 0, text, self.formats[row_format])
        if add_line:
            return self.writeline(sheet, row+1)
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


class TitledRange(object):
    FIRST_COL = 2
    ROW_INTERVAL = 3

    def __init__(self, sheet=None, first_row=None, content=None):
        self.sheet = sheet
        self.content = content
        first_data_col = TitledRange.FIRST_COL
        num_data_rows = len(self.content.row_names)

        if self.content.row_levels is not None:
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
        num_levels = len(self.content.row_levels) if self.content.row_levels is not None else 1

        #iterate over rows, incrementing current_row as we go
        for i, names_format in enumerate(zip(self.content.get_row_names(), self.content.get_row_formats())):
            names, row_format = names_format
            start_col = self.data_range.first_col - len(names)
            #emit row name(s)
            for n, name in enumerate(names):
                formats.write_rowcol_name(self.sheet, current_row, start_col+n, name, rc_row_align)
            #emit data if present
            savedata = False
            if self.content.data is not None:
                try:
                    for j, item in enumerate(self.content.data[i]):
                        formats.write_unlocked(self.sheet, current_row, self.data_range.first_col+j, item, row_format)
                    savedata = True # It saved successfully
                except:
                    errormsg = 'WARNING, failed to save "%s" with data:\n%s' % (self.content.name, self.content.data)
                    print(errormsg)
                    savedata = False
            if not savedata:
                for j in range(self.data_range.num_cols):
                    formats.write_empty_unlocked(self.sheet, current_row, self.data_range.first_col+j, row_format)
            #emit assumption
            if self.content.assumption:
                formats.write_option(self.sheet, current_row, self.data_range.last_col+1, name = self.content.assumption_properties['connector'])
                for index, col_name in enumerate(self.content.assumption_properties['columns']):
                    saveassumptiondata = False
                    if self.content.assumption_data is not None:
                        try:
                            assumptiondata = self.content.assumption_data[i]
                            if isinstance(assumptiondata, list): # Check to see if it's a list 
                                if len(assumptiondata)!=1: # Check to see if it has the right length
                                    errormsg = 'WARNING, assumption "%s" appears to have the wrong length:\n%s' % (self.content.name, assumptiondata)
                                    print(errormsg)
                                    saveassumptiondata = False
                                else: # It has length 1, it's good to go
                                    assumptiondata = assumptiondata[0] # Just pull out the only element
                            formats.write_unlocked(self.sheet, current_row, self.data_range.last_col+2+index, assumptiondata, row_format)
                            saveassumptiondata = True
                        except Exception as E:
                            errormsg = 'WARNING, failed to save assumption "%s" with data:\n%s\nError message:\n (%s)' % (self.content.name, self.content.assumption_data, repr(E))
                            print(errormsg)
                            saveassumptiondata = False
                            raise E
                    if not saveassumptiondata:
                        formats.write_empty_unlocked(self.sheet, current_row, self.data_range.last_col+2+index, row_format)
            current_row+=1
            if num_levels > 1 and ((i+1) % num_levels)==0: # shift between the blocks
                current_row +=1
        #done! return the new current_row plus spacing
        return current_row + TitledRange.ROW_INTERVAL # for spacing

    def param_refs(self, column_number = 0):
        return self.data_range.param_refs(self.sheet.get_name(), column_number)


class OptimaSpreadsheet:
    def __init__(self, name, pops, data_start=None, data_end=None, data=None, verbose=0, version=None):
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
        self.years_range = range(self.data_start, self.data_end+1)
        self.npops = len(pops)
        if version is None:
            version = supported_versions[-1]
            print(f'Warning: Creating a spreadsheet without a given version so defaulting to the latest version {version} which is compatible back to version {compatibledatabookversion(version)}')
        if compatibledatabookversion(version) is None:
            raise OptimaException(f'Cannot create an OptimaSpreadsheet with incompatible version {version}. Must be version {versions_different_databook[0]} or later.')
        self.version = version
            
    #############################################################################################################################
    ### Helper methods
    #############################################################################################################################

    def emit_years_block(self, name, current_row, row_names=None, ref_range=None, row_format=None, row_levels=None, row_formats=None, data=None, assumption_data=None, **kwargs):
        content = make_years_range(name=name, row_names=row_names, ref_range=ref_range, data_start=self.data_start, data_end=self.data_end, data=data)
        content.row_format = row_format
        content.assumption_data = assumption_data
        if row_levels is not None:  content.row_levels = row_levels
        if row_formats is not None: content.row_formats = row_formats
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row
        
    def emit_matrix_block(self, name, current_row, row_names=None, column_names=None, data=None, **kwargs):
        if column_names is None: column_names = self.getrange('allpops') # Not great to hardcode this, but this is always the case!
        content = OptimaContent(name=name, row_names=row_names, column_names=column_names, data=data)
        content.assumption = False
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats)
        return current_row

    def emit_constants_block(self, subheading, current_row, data):
        content = make_constant_range(subheading, data['name'], data['best'], data['low'], data['high'])
        content.assumption = False
        content.row_format = data['rowformat']
        the_range = TitledRange(self.current_sheet, current_row, content)
        current_row = the_range.emit(self.formats, rc_row_align = 'left')
        return current_row

    def formatkeydata(self, parname=None):
        '''
        Return key data in a format that can be written to spreadsheet
        Data in projects is formatted as [[best-pop1, best-pop2,... ], [low-pop1, low-pop2,... ], [high-pop1, high-pop2,... ]]
        This method reformats the key data so it's arranged as [high-pop1, best-pop1, low-pop1, high-pop1, best-pop2, low-pop2, ... ]
        '''
        if self.data is not None:
            data = self.data.get(parname)
            if data is not None: 
                newdata = []
                assumption = []
                npops = len(data[0]) 
                npts = self.data_end-self.data_start+1
                for pop in range(npops):
                    for est in [2,0,1]: # Looping though best/low/high
                        if len(data[est][pop])==1: # It's an assumption
                            newdata.append(['']*npts)
                            assumption.append(data[est][pop])
                        elif len(data[est][pop]) > 1: # It's data
                            newdata.append(nan2blank(padunpad(name=parname, datarow=data[est][pop], datayears=self.data['years'], startyear=self.data_start, endyear=self.data_end)))
                            assumption.append('')
                return (newdata, assumption)
        return (None, None) # By default, return None

    def formattimedata(self, parname=None):
        ''' Return standard time data in a format that can be written to spreadsheet'''
        if self.data is not None:
            data = self.data.get(parname)
            if data is not None: 
                newdata = []
                assumption = []
                npops = len(data) # Data in projects is formatted as [pop1, pop2, ... ]
                npts = self.data_end-self.data_start+1
                for pop in range(npops):
                    if len(data[pop])==1: # It's an assumption
                        newdata.append(['']*npts)
                        assumption.append(nan2blank(data[pop])[0])
                    elif len(data[pop]) > 1: # It's data
                        newdata.append(nan2blank(padunpad(name=parname, datarow=data[pop], datayears=self.data['years'], startyear=self.data_start, endyear=self.data_end)))
                        assumption.append('')
                return (newdata, assumption)
        return (None, None) # By default, return None
    
    def getmatrixdata(self, parname=None):
        ''' Get matrix data -- stored directly so just have to retrieve'''
        if self.data is not None:
            origdata = self.data.get(parname)
            data = []
            for row in origdata: data.append(zero2blank(row))
            return (data, None)
        return (None, None) # By default, return None
    
    def getrange(self, rangename):
        ''' Little helper function to make range names more palatable '''
        if    rangename=='allpops':  return self.ref_pop_range
        elif  rangename=='females':  return self.ref_females_range
        elif  rangename=='males':    return self.ref_males_range
        elif  rangename=='children': return self.ref_child_range
        elif  rangename=='average':  return ['Average']
        elif  rangename=='total':    return ['Total']
        elif  rangename=='hbl':      return ['high','best','low']
        elif  rangename=='.':        return None
        else: 
            errormsg = 'Range name %s not found' % rangename
            raise Exception(errormsg)
        return None
    

    #############################################################################################################################
    ### Actually make the sheets
    #############################################################################################################################

    def generate_instructions(self):
        self.current_sheet = self.sheets['Instructions'] # OK to hard-code since function is hardcoded itself
        current_row = 0
        self.current_sheet.set_column('A:A',120)
        self.current_sheet.merge_range('A1:A3', 'O P T I M A   H I V', self.formats.formats['info_header'])
        current_row = 3
        current_row = self.formats.writeline(self.current_sheet, current_row)
        current_row = self.formats.writeblock(self.current_sheet, current_row, row_height=30, text='Welcome to the Optima HIV data entry spreadsheet. This is where all data for the model will be entered. Please ask someone from the Optima development team if you need help, or use the default contact (info@optimamodel.com).')
        current_row = self.formats.writeblock(self.current_sheet, current_row, text='For further details please visit: http://optimamodel.com/indicator-guide')
        current_row = self.formats.writeblock(self.current_sheet, current_row, text='Spreadsheet created with Optima version %s' % self.version)
        current_row = self.formats.writeblock(self.current_sheet, current_row, text='Date created: %s' % getdate(today()))
        current_row = self.formats.writeblock(self.current_sheet, current_row, row_height=80, add_line=False, text='After you upload this spreadsheet to your Optima HIV project, your data will be stored in the project but any comments you make on individual cells will NOT be stored. You are therefore encouraged to enter any specific comments that you would like to make about this data spreadsheet in the shaded cells below. These comments will be stored. We recommend that you insert a link to the project logbook in one of these cells.')
        current_row = self.formats.writeline(self.current_sheet, current_row, row_format='bold')
        current_row = self.formats.writeblock(self.current_sheet, current_row, add_line=False, row_format='bold', text='Comments:')
        ncommentrows = 15 # Add comment rows
        for ncr in range(ncommentrows):
            try:    thistext = self.data['meta']['datacomments'][ncr] # Try to read comments
            except: thistext = '' # If failure, skip
            current_row = self.formats.writeblock(self.current_sheet, current_row, row_format='orange', add_line=False, text=thistext)


    def generate_populations(self):
        self.current_sheet = self.sheets['Populations'] # OK to hard-code since function is hardcoded itself
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


    def generate_sheets(self, sheetname):
        
        if self.verbose>2: print('Generating %s' % sheetname)
        current_row = 0
        pardefs = self.pardefinitions['sheetcontent'][sheetname]
        sheettype = pardefs[0]['type']
        
        # For matrices, change the column width
        if sheettype=='matrix':
            for ind in range(len(self.pops)):
                self.current_sheet.set_column(2+ind,2+ind,12)
        
        # Loop over each parameter in this sheet
        for pd in pardefs:
            if pd['type']=='matrix': # Handle matrix special case
                row_levels = None
                datamethod = self.getmatrixdata
                emitmethod = self.emit_matrix_block
            elif pd['type']=='key': # Handle key data (population size, prevalence) special case
                row_levels = ['high', 'best', 'low']
                datamethod = self.formatkeydata
                emitmethod = self.emit_years_block
            else: # Everything else
              row_levels = None
              datamethod = self.formattimedata
              emitmethod = self.emit_years_block
            (data, assumption_data) = datamethod(pd['short'])
            current_row = emitmethod(pd['name'], current_row, row_names=self.getrange(pd['rownames']), row_format=pd['rowformat'], row_levels=row_levels, data=data, assumption_data=assumption_data)
        return None
    
    
    def generate_constants(self):
        self.current_sheet = self.sheets['Constants'] # OK to hard-code since function is hardcoded itself
        self.current_sheet.set_column(1,1,40)
        current_row = 0
        
        # Parse data
        constdata = odict()
        constdefs = self.pardefinitions['Data constants'] # Shorten name
        for const in constdefs:
            sub = const['subheading']
            if sub not in constdata.keys(): # Create new list if sheet not encountered yet
                constdata[sub] = {'name':[], 'best':[], 'low':[], 'high':[], 'format':None} # Initialize -- parameter names, values, and format
            for key in ['name', 'best' ,'low', 'high']:
                constdata[sub][key].append(const[key])
            constdata[sub]['rowformat'] = const['rowformat'] # Same for all
            
        # Generate spreadsheet by subheading
        for (thisname, thisdata) in constdata.items():
            current_row = self.emit_constants_block(thisname, current_row, thisdata)
        return None


    def create(self, path):
        
        # Load definitions
        self.pardefinitions = loaddatapars(verbose=self.verbose)
        
        # Preliminaries
        if self.verbose >=1: 
            print('Creating spreadsheet %s with parameters: npops = %s, datastart = %s, dataend = %s' % (path, self.npops, self.data_start, self.data_end))
        self.book = xlsxwriter.Workbook(path)
        self.formats = OptimaFormats(self.book)
        self.sheets = {}
        
        # Actually generate workbooks
        self.sheet_names = list(self.pardefinitions['sheets'].keys())
        for sheetname in ['Instructions', 'Populations']+self.sheet_names:
            self.sheets[sheetname] = self.book.add_worksheet(sheetname)
        self.sheet_names.remove('Constants') # Remove constants key which is handled separately
        self.generate_instructions() # Instructions
        self.generate_populations() # Population metadata
        for sheetname in self.sheet_names:
            self.current_sheet = self.sheets[sheetname]
            self.generate_sheets(sheetname)
        self.generate_constants() # Handle constants
        self.book.close()
        return None





class OptimaProgramSpreadsheet:
    def __init__(self, name, pops, progs, data_start=None, data_end=None, verbose = 0):
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
        self.years_range = range(int(self.data_start), int(self.data_end+1))

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
        current_row = self.formats.writeline(self.current_sheet, current_row)
        current_row = self.formats.writeblock(self.current_sheet, current_row, row_height=65, text='Welcome to the Optima HIV program data entry spreadsheet. This is where all program data will be entered. Please ask someone from the Optima development team if you need help, or use the default contact (info@optimamodel.com).')
        current_row = self.formats.writeblock(self.current_sheet, current_row, text='For further details please visit: http://optimamodel.com/file/indicator-guide')


    def emit_years_block(self, name, current_row, row_names, row_format = OptimaFormats.GENERAL,
        assumption = False, row_levels = None, row_formats = None):
        content = make_years_range(name=name, row_names=row_names, data_start=self.data_start, data_end=self.data_end)
        content.row_format = row_format
        content.assumption = assumption
        if row_levels is not None:
            content.row_levels = row_levels
        if row_formats is not None:
            content.row_formats = row_formats
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
