from flask import Flask
from generators.line import generatedata
import json

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def root():
    return 'API is running!'

@app.route('/api/data/line', methods=['GET'])
def line():
    return app.send_static_file('line-chart.json')

@app.route('/api/data/line/<int:numpoints>', methods=['GET'])
def lineParam(numpoints):
    return json.dumps({
        'values': generatedata(numpoints),
        "key": "Line series",
        "color": "#ff7f0e"
    })

@app.route('/api/data/stacked-area', methods=['GET'])
def stackedArea():
    return app.send_static_file('stacked-area-chart.json')

@app.route('/api/data/multi-bar', methods=['GET'])
def multiBar():
    return app.send_static_file('multi-bar-chart.json')

@app.route('/api/data/pie', methods=['GET'])
def pie():
    return app.send_static_file('pie-chart.json')

@app.route('/api/data/line-scatter-error', methods=['GET'])
def lineScatterError():
    return app.send_static_file('line-scatter-error-chart.json')


@app.route('/api/data/download', methods=['GET'])
def downloadExcel():
    return app.send_static_file('example.xlsx')

if __name__ == '__main__':
    app.run(debug=True)
