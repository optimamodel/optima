import json
from flask import Blueprint
from flask.ext.login import login_required
from generators.line import generatedata

# route prefix: /api/data
data = Blueprint('data',  __name__, static_folder = '../static')

@data.route('/line', methods=['GET'])
@login_required
def line():
    """ mocks up data for line graph """
    return data.send_static_file('line-chart.json')

@data.route('/line/<int:numpoints>', methods=['GET'])
@login_required
def lineParam(numpoints):
    """ mocks up data for line graph with generated data """
    return json.dumps({
        'values': generatedata(numpoints),
        "key": "Line series",
        "color": "#ff7f0e"
    })

@data.route('/stacked-area', methods=['GET'])
@login_required
def stackedArea():
    """ mocks up data for stacked area """
    return data.send_static_file('stacked-area-chart.json')

@data.route('/multi-bar', methods=['GET'])
@login_required
def multiBar():
    """ mocks up data for multi bar area """
    return data.send_static_file('multi-bar-chart.json')

@data.route('/pie', methods=['GET'])
@login_required
def pie():
    """ mocks up data for pie graph """
    return data.send_static_file('pie-chart.json')

@data.route('/line-scatter-error', methods=['GET'])
@login_required
def lineScatterError():
    """ mocks up data for line scatter graph with errors """
    return data.send_static_file('line-scatter-error-chart.json')

@data.route('/line-area-scatter', methods=['GET'])
@login_required
def lineAreaScatter():
    """ mocks up data for line scatter graph """
    return data.send_static_file('line-area-scatter-chart.json')
