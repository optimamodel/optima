from flask import Flask

app = Flask(__name__)

@app.route('/')
def root():
    return 'API is running!'

@app.route('/data/line')
def line():
    return app.send_static_file('line-chart.json')

@app.route('/data/stacked-area')
def stackedArea():
    return app.send_static_file('stacked-area-chart.json')

@app.route('/data/multi-bar')
def multiBar():
    return app.send_static_file('multi-bar-chart.json')

@app.route('/data/pie')
def pie():
    return app.send_static_file('pie-chart.json')

@app.route('/data/line-scatter-error')
def lineScatterError():
    return app.send_static_file('line-scatter-error-chart.json')


if __name__ == '__main__':
    app.run()
