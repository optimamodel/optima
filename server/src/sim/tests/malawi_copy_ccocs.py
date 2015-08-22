# This script reads the calibrated legacy json files and applies
# the following fixes:
# 	- Copies national programs into the district
#	- Rescales the funding by the district's relative population

import add_optima_paths
from portfolio import Portfolio
from region import Region
from sim import Sim
from extra_utils import dict_equal
from copy import deepcopy
from makeccocs import convertparams
import os

malawi = Region.load('./regions/Malawi 150820.json')

# D = malawi.D

# print D['programs'][1]['ccparams']
# print D['programs'][1]['convertedccparams']
# import sys
# sys.exit()

path_prefix = "./regions"
#path_prefix = "C:/Users/romesh/Google Drive/Optima/Country applications/Malawi/Data/District level/Project files/"
for fname in [x for x in os.listdir(path_prefix) if x.endswith('json')]:
	district = Region.load(path_prefix+fname)

	# Copy the national programs into the district
	district.metadata['programs'] = deepcopy(malawi.metadata['programs'])

	# Calculate the relative population size
	relative_popsize = district.calibrations[0]['popsize'].sum()/malawi.calibrations[0]['popsize'].sum()

	# print district.metadata['programs'][0]['ccparams']['funding']

	# Rescale funding and recalculate converted CCOC params
	progs = district.metadata['programs'] # Note - this is a reference
	#print 'INITIAL', district.metadata['programs'][1]['ccparams']['funding']

	coverage_params = ['numcircum','numost','numpmtct','numfirstline','numsecondline']
	for prognumber in xrange(0,len(progs)): # Loop over programs
	    if len(progs[prognumber].get('effects')): # If the programs has effects.... (otherwise it's a fixed cost program)
	    # WARNING - shoudn't spending-only programs have scaled costs as well??
	        progs[prognumber]['ccparams']['funding'] *= relative_popsize
	        # print progs[prognumber]['ccparams']
	        # print progs[prognumber]['convertedccparams'] 
	        progs[prognumber]['convertedccparams'] = convertparams(ccparams=progs[prognumber]['ccparams'])
	        # print progs[prognumber]['convertedccparams'] 
	        # import sys
	        # sys.exit()
	        for effectnumber, effect in enumerate(progs[prognumber]['effects']):
	            parname = effect['param']
	            if parname not in coverage_params: # Only going to make cost-outcome curves for programs where the affected parameter is not coverage
	                convertedccoparams = deepcopy(progs[prognumber]['convertedccparams'])
	                convertedcoparams = effect['convertedcoparams']
	                coparams = effect['coparams']
	                convertedccoparams[0].extend([convertedcoparams[0],convertedcoparams[2]])
	                convertedccoparams[1].extend([coparams[0],coparams[2]])
	                convertedccoparams[2].extend([coparams[1],coparams[3]])

	                progs[prognumber]['effects'][effectnumber]['convertedccoparams'] = convertedccoparams 

	# print 'FINAL', district.metadata['programs'][1]['ccparams']['funding']
	# import sys
	# sys.exit()

	district.D['programs'] = deepcopy(district.metadata['programs']) # the metadata variable is the master copy
	district.save(path_prefix+fname.replace('.json','_oop.json'))

	        