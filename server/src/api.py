from flask import Flask

app = Flask(__name__)

@app.route('/api')
def root():
    return 'API is running!'

@app.route('/api/data/line')
def line():
    return app.send_static_file('line-chart.json')

@app.route('/api/data/stacked-area')
def stackedArea():
    return app.send_static_file('stacked-area-chart.json')

@app.route('/api/data/multi-bar')
def multiBar():
    return app.send_static_file('multi-bar-chart.json')

@app.route('/api/data/pie')
def pie():
    return app.send_static_file('pie-chart.json')

@app.route('/api/data/line-scatter-error')
def lineScatterError():
    return app.send_static_file('line-scatter-error-chart.json')


if __name__ == '__main__':
    app.run()
