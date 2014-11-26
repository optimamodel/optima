import json
from flask import Blueprint
from flask.ext.login import login_required
from generators.line import generatedata

""" route prefix: /api/data """
data = Blueprint('data',  __name__, static_folder = '../static')

""" mocks up data for line graph """
@data.route('/line', methods=['GET'])
@login_required
def line():
    return data.send_static_file('line-chart.json')

""" mocks up data for line graph with generated data """
@data.route('/line/<int:numpoints>', methods=['GET'])
@login_required
def lineParam(numpoints):
    return json.dumps({
        'values': generatedata(numpoints),
        "key": "Line series",
        "color": "#ff7f0e"
    })

""" mocks up data for stacked area """
@data.route('/stacked-area', methods=['GET'])
@login_required
def stackedArea():
    return data.send_static_file('stacked-area-chart.json')

""" mocks up data for multi bar area """
@data.route('/multi-bar', methods=['GET'])
@login_required
def multiBar():
    return data.send_static_file('multi-bar-chart.json')

""" mocks up data for pie graph """
@data.route('/pie', methods=['GET'])
@login_required
def pie():
    return data.send_static_file('pie-chart.json')

""" mocks up data for line scatter graph with errors """
@data.route('/line-scatter-error', methods=['GET'])
@login_required
def lineScatterError():
    return data.send_static_file('line-scatter-error-chart.json')

""" mocks up data for line scatter graph """
@data.route('/line-scatter-area', methods=['GET'])
@login_required
def lineScatterArea():
    return data.send_static_file('line-scatter-area-chart.json')
