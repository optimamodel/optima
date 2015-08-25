# This script loads a json file and prints out the convertedccparams and convertedcoparams
# for all coverage-type programs

import add_optima_paths
from region import Region
from copy import deepcopy
import simbox
from makeccocs import ccoeqn, cceqn, cc2eqn, cco2eqn, coverage_params, makesamples
from numpy import nan, zeros, array, isnan
from utils import sanitize, perturb
from getcurrentbudget import getcurrentbudget
from timevarying import timevarying
from makemodelpars import makemodelpars

r = Region.load('./regions/georgia_working.json')
D = r.D
alloc = D['data']['origalloc']

 # Set defaults, stored as [median, lower bound, upperbound]. ONLY for use in BE. In FE, if ccocs haven't been defined then the user won't get to this step
default_convertedccparams = [[0.8, 4.9e-06], [0.8, 4.7e-06], [0.8, 5.1e-06]]
default_convertedccoparams = [[0.8, 4.9e-06, 0.4, 0.8, 0], [0.8, 4.7e-06, 5.1e-06, 0.4, 0.8, 0], [0.8, 4.9e-06, 0.4, 0.8, 0]]

budget = timevarying(alloc, ntimepm = 1, nprogs = len(alloc), tvec =r.options['partvec'])
D, currentcoverage, currentnonhivdalysaverted = getcurrentbudget(D, alloc=budget, randseed=None)
M = makemodelpars(D['P'],D['opt'],withwhat='c')
print 'M numost = ',M['numost'][0]
print 'M pmtct = ',M['numpmtct'][0]

for prognumber, progname in enumerate(D['data']['meta']['progs']['short']):
	program_ccparams = D['programs'][prognumber]['convertedccparams']
	spending = alloc[prognumber]

	use_default_ccparams = not program_ccparams or (not isinstance(program_ccparams, list) and isnan(program_ccparams))
	temp =  program_ccparams if not use_default_ccparams else default_convertedccparams
	convertedccparams = deepcopy(temp)
	currentcoverage = cc2eqn(spending, convertedccparams[0]) if len(convertedccparams[0])==2 else cceqn(spending, convertedccparams[0])

	for effectnumber, effect in enumerate(D['programs'][prognumber]['effects']):
	    popname, parname = effect['popname'], effect['param']
	    if parname in coverage_params:
	        print "%s - origalloc = %.4f, saturation = %.4f, Coverage = %.4f" % (progname,spending,convertedccparams[0][0],currentcoverage)
	        print D['data']['costcov']['cov'][prognumber]




