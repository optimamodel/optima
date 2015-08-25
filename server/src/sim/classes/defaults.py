# -*- coding: utf-8 -*-
"""
Created on Tue Jun 02 00:08:51 2015

@author: David Kedziora
"""
current_version = 5

### OPTIMISATION DEFAULTS
maxiters = 1e3
timelimit = 30#5.01#600

### OBJECTIVE DEFAULTS
startenduntil = [2015, 2030, 2030]
#incidalydeathcost = [True, False, False, False]
#incidalydeathcostweight = [100.0, 100.0, 100.0, 100.0]
incidalydeathcost = [False, True, False, False]
incidalydeathcostweight = [100.0, 100.0, 100.0, 100.0]

### REGION DEFAULTS

# Region information for default example project
datastart = 2000
dataend = 2015
nsims = 5
pops = [{u'name': u'Female sex workers', u'short_name': u'FSW', u'sexworker': True, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Clients of sex workers', u'short_name': u'Clients', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': True, u'female': False, u'male': True, u'sexwomen': True}]
progs = [{u'category': u'Prevention', u'short_name': u'Condoms', u'name': u'Condom promotion and distribution', u'parameters': [{u'value': {u'pops': [u''], u'signature': [u'condom', u'reg']}}, {u'value': {u'pops': [u''], u'signature': [u'condom', u'cas']}}]}]

# Region information for Haiti project - to go with Haiti.json
haiti = {}
haiti['datastart'] = 2000
haiti['dataend'] = 2020
haiti['populations'] = [{u'name': u'Female sex workers', u'short_name': u'FSW', u'sexworker': True, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Clients of sex workers', u'short_name': u'Clients', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': True, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Men who have sex with men', u'short_name': u'MSM', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': False, u'male': True, u'sexwomen': False}, {u'name': u'Male Children (0-14)', u'short_name': u'Male children 0\u201014', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': False}, {u'name': u'Female Children (0-14)', u'short_name': u'Female Children 0-14', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Males (15-19)', u'short_name': u'Males 15-19', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Females (15-19)', u'short_name': u'Females 15-19', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Males (20-24)', u'short_name': u'Males 20-24', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Females (20-24)', u'short_name': u'Females 20-24', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Males (25-49)', u'short_name': u'Males 25-49', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Females (25-49)', u'short_name': u'Females 25-49', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Males (50+)', u'short_name': u'Males 50+', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': False, u'female': False, u'male': True, u'sexwomen': True}, {u'name': u'Females (50+)', u'short_name': u'Females 50+', u'sexworker': False, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}]
haiti['programs'] = [{u'category': u'Prevention', u'short_name': u'Condom Programs', u'name': u'Condom programs for general population and the commercial sex community', u'parameters': [{u'value': {u'pops': [u'Males 15-19'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Females 15-19'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Males 20-24'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Females 20-24'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Males 25-49'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Females 25-49'], u'signature': [u'condom', u'cas']}}]}, {u'category': u'Prevention', u'short_name': u'SBCC', u'name': u'Social and behavior change communication', u'parameters': [{u'value': {u'pops': [u'Males 15-19'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Females 15-19'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Males 20-24'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Females 20-24'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Males 25-49'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Females 25-49'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'Males 15-19'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Females 15-19'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Males 20-24'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Females 20-24'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Males 25-49'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Females 25-49'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Males 50+'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Females 50+'], u'signature': [u'hivtest']}}]}, {u'category': u'Prevention', u'short_name': u'FSW programs', u'name': u'Programs for female sex workers and clients', u'parameters': [{u'value': {u'pops': [u'Clients'], u'signature': [u'condom', u'com']}}, {u'value': {u'pops': [u'FSW'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Clients'], u'signature': [u'hivtest']}}]}, {u'category': u'Prevention', u'short_name': u'MSM programs', u'name': u'Programs for men who have sex with men', u'parameters': [{u'value': {u'pops': [u'MSM'], u'signature': [u'condom', u'cas']}}, {u'value': {u'pops': [u'MSM'], u'signature': [u'hivtest']}}]}, {u'category': u'Prevention', u'short_name': u'HTC', u'name': u'HIV testing and counseling', u'parameters': [{u'value': {u'pops': [u'Males 15-19'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Females 15-19'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Males 20-24'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Females 20-24'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Males 25-49'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Females 25-49'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Males 50+'], u'signature': [u'hivtest']}}, {u'value': {u'pops': [u'Females 50+'], u'signature': [u'hivtest']}}]}, {u'category': u'Care and treatment', u'short_name': u'ART', u'name': u'Antiretroviral therapy', u'parameters': [{u'value': {u'pops': [u''], u'signature': [u'txtotal']}}]}, {u'category': u'Prevention', u'short_name': u'PMTCT', u'name': u'Prevention of mother-to-child transmission', u'parameters': [{u'value': {u'pops': [u''], u'signature': [u'numpmtct']}}]}, {u'category': u'Other', u'short_name': u'OVC', u'name': u'Orphans and vulnerable children', u'parameters': []}, {u'category': u'Care and treatment', u'short_name': u'Other care', u'name': u'Care & Support', u'parameters': []}, {u'category': u'Management and administration', u'short_name': u'MGMT', u'name': u'Management', u'parameters': []}, {u'category': u'Management and administration', u'short_name': u'HR', u'name': u'HR and training', u'parameters': []}, {u'category': u'Management and administration', u'short_name': u'ENV', u'name': u'Enabling environment', u'parameters': []}, {u'category': u'Other', u'short_name': u'SP', u'name': u'Social protection', u'parameters': []}, {u'category': u'Other', u'short_name': u'M&E', u'name': u'Monitoring, evaluation, surveillance, and research', u'parameters': []}, {u'category': u'Prevention', u'short_name': u'Other Prevention', u'name': u'Other Prevention', u'parameters': []}]

### METADATA DEFAULTS
# These are the HIV constants

from numpy import arange

metadata = {}
metadata['healthstates'] = ['acute', 'gt500', 'gt350', 'gt200', 'gt50', 'aids']
metadata['ncd4'] = len(metadata['healthstates'])
metadata['nstates'] = 1+metadata['ncd4']*5 # Five are undiagnosed, diagnosed, 1st line, failure, 2nd line, plus susceptible
metadata['sus']  = arange(0,1)
metadata['undx'] = arange(0*metadata['ncd4']+1, 1*metadata['ncd4']+1)
metadata['dx']   = arange(1*metadata['ncd4']+1, 2*metadata['ncd4']+1)
metadata['tx1']  = arange(2*metadata['ncd4']+1, 3*metadata['ncd4']+1)
metadata['fail'] = arange(3*metadata['ncd4']+1, 4*metadata['ncd4']+1)
metadata['tx2']  = arange(4*metadata['ncd4']+1, 5*metadata['ncd4']+1)
for i,h in enumerate(metadata['healthstates']): 
	metadata[h] = [metadata[state][i] for state in ['undx', 'dx', 'tx1', 'fail', 'tx2']]


program = {}
program['ccparams'] = {}
program['ccparams']['function'] = 'cceqn' # Use this dictionary to load/save
program['ccparams']['parameters'] = {u'coveragelower': 0.2, u'nonhivdalys': 0.0, u'funding': 300000.0, u'saturation': 0.98, u'coverageupper': 0.75, u'scaleup': 0.73}

program['coparams'] = []
program['coparams'].append({'function':'coeqn','parameters':[0.2, 0.25, 0.8, 0.85]})


