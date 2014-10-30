import os
from flask import Flask
from flask import helpers
from flask import request
from werkzeug import secure_filename
from generators.line import generatedata
import json
import traceback
import sys
from sim.dataio import loaddata
from sim.dataio import savedata
from sim.updatedata import updatedata

UPLOAD_FOLDER = '/tmp/uploads' #todo configure
ALLOWED_EXTENSIONS=set(['txt','xlsx','xls'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

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

@app.route('/api/data/line-scatter-area', methods=['GET'])
def lineScatterArea():
    return app.send_static_file('line-scatter-area-chart.json')


@app.route('/api/data/download/<downloadName>', methods=['GET'])
def downloadExcel(downloadName):
    example_excel_file_name = 'example.xlsx'

    file_path = helpers.safe_join(app.static_folder, example_excel_file_name)
    options = {
        'cache_timeout': app.get_send_file_max_age(example_excel_file_name),
        'conditional': True,
        'attachment_filename': downloadName
    }
    return helpers.send_file(file_path, **options)

@app.route('/api/data/upload', methods=['POST'])
def uploadExcel():
    reply = {'status':'NOK'}
    try:
        loaddir = app.config['UPLOAD_FOLDER']
        example_prj = 'example.prj'
        try: 
            example_in_filename = helpers.safe_join(app.static_folder, example_prj)
            example_out_filename = helpers.safe_join(loaddir, example_prj)
            data = loaddata(example_in_filename)
            savedata(example_out_filename)
        except Exception, err:
            var = traceback.format_exc()
            print(var)
            # eat it here
            
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            reply['file'] = filename
            if allowed_file(filename):
                server_filename = os.path.join(loaddir, filename)
                file.save(server_filename)
                file_basename, file_extension = os.path.splitext(filename)
                out_filename = updatedata(file_basename, loaddir)
                data = loaddata(server_filename)
#                epi_file_name = 'epi-template.xlsx'
#                file_path = helpers.safe_join(app.static_folder, epi_file_name)

 #               data = loaddata(server_filename) #gives an error for an example file...
                reply['status'] = 'OK'
                print(data)
            else:
                reply['reason'] = 'invalid file extension:'+ filename
    except Exception, err:
        var = traceback.format_exc()
        print(var)
        reply['exception'] = var
    return json.dumps(reply)

if __name__ == '__main__':
    app.run(debug=True)
