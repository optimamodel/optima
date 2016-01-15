#!/bin/env python
# -*- coding: utf-8 -*-
from optima_test_base import OptimaTestCase
from collections import OrderedDict
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
#        print "def_parset", def_parset
        dumped_parset = json.dumps(def_parset, cls=OptimaJSONEncoder)
#        print "dumped_parset", dumped_parset
        self.assertTrue(dumped_parset)
        restored_parset = json.loads(dumped_parset, object_pairs_hook=OrderedDict)
#        print "json_load", json_load
        print restored_parset['pars'][0].keys(), def_parset.pars[0].keys()
        print restored_parset.keys(), def_parset.__dict__.keys()
        self.assertTrue(restored_parset.keys() == def_parset.__dict__.keys())
        self.assertTrue(restored_parset['pars'][0].keys() == def_parset.pars[0].keys())
