
from optima.parameters import loadpartable

parameter_list = loadpartable()

def input_parameter(short):
    entry = [param for param in parameter_list if short in param['short']]
    if entry:
        return entry[0]
    else:
        return None

def input_parameters(short):
    return [param for param in parameter_list if short in param['short']]

def input_parameter_name(short):
    param = input_parameter(short)
    if param:
        return param['name']
    else:
        return None

# TODO: is this still necessary??
def parameter_name(key): #params is the output of parameters() method
    if not type(key)==list: key=[key]
    entry = [param for param in parameter_list if ''.join(param['short'])==''.join(key)]
    if entry:
        return entry[0]['name']
    else:
        return None

