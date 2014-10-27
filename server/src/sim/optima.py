"""
OPTIMA

This function does everything. The basic procedure is as follows:

1. loaddata -- load the data into a structure
2. data2pars -- convert the data into model parameters
3. setupmodel -- reconcile partnerships and calculate parameters to go into the model
4. model -- actually run the model

Version: 2014sep24
"""

## Set parameters
filename = 'example.xlsx'


print('WELCOME TO OPTIMA')
from loaddata import loaddata
from data2pars import data2pars

data = loaddata(filename)
P = data2pars(data)

print('Done.')
