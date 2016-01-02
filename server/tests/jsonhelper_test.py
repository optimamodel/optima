#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
import unittest
import json
from server.api import app
from flask import helpers
from uuid import uuid4
import optima as op
from server.webapp.jsonhelper import normalize_dict, OptimaJSONEncoder


class JsonHelperTestCase(unittest.TestCase):

    def test_default_parset(self):
        p = op.Project()
        example_excel_file_name = 'test.xlsx'
        file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
        p.loadspreadsheet(file_path)
        def_parset = p.parsets['default']
        self.assertTrue(def_parset)
        json_dump = json.dumps(def_parset, cls=OptimaJSONEncoder)
#        print "json_dump", json_dump
        self.assertTrue(json_dump)
        json_load = json.loads(json_dump)
#        print "json_load", json_load
        ps = json_load['Parameterset']
        self.assertTrue(ps.keys() == def_parset.__dict__.keys())
        self.assertTrue(set(ps['pars'][0].keys()) == set(def_parset.pars[0].keys()))
