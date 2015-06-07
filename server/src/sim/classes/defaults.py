# -*- coding: utf-8 -*-
"""
Created on Tue Jun 02 00:08:51 2015

@author: David Kedziora
"""

datastart = 2000
dataend = 2015
nsims = 5
pops = [{u'name': u'Female sex workers', u'short_name': u'FSW', u'sexworker': True, u'injects': False, u'sexmen': True, u'client': False, u'female': True, u'male': False, u'sexwomen': False}, {u'name': u'Clients of sex workers', u'short_name': u'Clients', u'sexworker': False, u'injects': False, u'sexmen': False, u'client': True, u'female': False, u'male': True, u'sexwomen': True}]
progs = [{u'category': u'Prevention', u'short_name': u'Condoms', u'name': u'Condom promotion and distribution', u'parameters': [{u'value': {u'pops': [u''], u'signature': [u'condom', u'reg']}}, {u'value': {u'pops': [u''], u'signature': [u'condom', u'cas']}}]}]

current_version = 5