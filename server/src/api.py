import os
import shutil
from flask import Flask
from flask import helpers
from flask import request
from flask import jsonify
from flask import session
from werkzeug import secure_filename
from generators.line import generatedata
import json
import traceback
import sys
from sim.dataio import loaddata, savedata, normalize_file, DATADIR
from sim.updatedata import updatedata
from sim.loaddata import loaddata
from sim.makeproject import makeproject
from sim.manualfit import manualfit
from sim.bunch import unbunchify
from sim.runsimulation import runsimulation
from sim.optimize import optimize

UPLOAD_FOLDER = DATADIR #'/tmp/uploads' #todo configure
ALLOWED_EXTENSIONS=set(['txt','xlsx','xls'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'

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

@app.route('/api/calibrate/manual', methods=['POST'])
def doManualCalibration():
    data = json.loads(request.data)
    fits = manualfit(data)
    print("fits: %s" % fits)
    fits = [unbunchify(x) for x in fits]
    print("unbunchified fits: %s" % fits)
    return jsonify(fits[0])

@app.route('/api/project/create/<projectName>')
# expects json with the following arguments (see example):
# {"npops":6,"nprogs":8, "datastart":2000, "dataend":2015}
def createProject(projectName):
    session.clear()
    print("createProject %s" % projectName)
    data = json.loads(request.args.get('params'))
    data = dict([(x,int(y)) for (x,y) in data.items()])
    print(data)
    makeproject_args = {"projectname":projectName}
    makeproject_args = dict(makeproject_args.items() + data.items())
    print(makeproject_args)
    new_project_template = makeproject(**makeproject_args) # makeproject is supposed to return the name of the existing file...
    print("new_project_template: %s" % new_project_template)
    (dirname, basename) = os.path.split(new_project_template)
    xlsname = projectName + '.xlsx'
    srcfile = helpers.safe_join(app.static_folder,'epi-template.xlsx')
    dstfile =  helpers.safe_join(dirname, xlsname)
    shutil.copy(srcfile, dstfile)

    return helpers.send_from_directory(dirname, xlsname)

@app.route('/api/project/open/<projectName>')
# expects project name, will put it into session
# todo: only if it can be found
def openProject(projectName):
    session.clear()
    session['projectName'] = projectName
    return jsonify({'status':'OK', 'projectName':projectName})

@app.route('/api/calibrate/view', methods=['POST'])
def doRunSimulation():
    data = json.loads(request.data)
    #expects json: {"projectdatafile:<name>,"startyear":year,"endyear":year}
    args = {"loaddir": app.static_folder}
    projectdatafile = data.get("projectdatafile")
    if projectdatafile:
        args["projectdatafile"] = helpers.safe_join(app.static_folder, projectdatafile)
    startyear = data.get("startyear")
    if startyear:
        args["startyear"] = int(startyear)
    endyear = data.get("endyear")
    if endyear:
        args["endyear"] = int(endyear)
    data_file_path = runsimulation(**args) 
    options = {
        'cache_timeout': app.get_send_file_max_age(example_excel_file_name),
        'conditional': True,
        'attachment_filename': downloadName
    }
    return helpers.send_file(data_file_path, **options)

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
    file = request.files['file']
    loaddir = app.config['UPLOAD_FOLDER']
    if not file:
        reply['reason'] = 'No file is submitted!'
        return json.dumps(reply)

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        reply['reason'] = 'File type of %s is not accepted!' % filename
        return json.dumps(reply)

    file_basename, file_extension = os.path.splitext(filename)
    project_name = helpers.safe_join(loaddir, file_basename+'.prj')
    print("project name: %s" % project_name)
    if not os.path.exists(project_name):
        reply['reason'] = 'Project %s does not exist' % file_basename
        return json.dumps(reply)

    try:
        out_filename = updatedata(file_basename, loaddir)
        data = loaddata(project_name)
    except Exception, err:
        var = traceback.format_exc()
        reply['exception'] = var
        return json.dumps(reply)      

    reply['status'] = 'OK'
    reply['result'] = 'Project %s is updated' % file_basename
    return json.dumps(reply)

@app.route('/api/analysis/optimisation/define/<defineType>', methods=['POST'])
def defineObjectives(defineType):
    data = json.loads(request.data)
    json_file = os.path.join(app.config['UPLOAD_FOLDER'], "optimisation.json")
    with open(json_file, 'w') as outfile:
        json.dump(data, outfile)
    return json.dumps({'status':'OK'})

@app.route('/api/analysis/optimisation/start')
def runOptimisation():
    # should call method in optimize.py but it's not implemented yet. for now just returns back the file
    json_file = os.path.join(app.config['UPLOAD_FOLDER'], "optimisation.json")
    if (not os.path.exists(json_file)):
        return json.dumps({"status":"NOK", "reason":"Define the optimisation objectives first"})
    with open(json_file, 'r') as infile:
        data = json.load(infile)
    (lineplot, dataplot) = optimize()
    (lineplot, dataplot) = (unbunchify(lineplot), unbunchify(dataplot))
    return json.dumps({"lineplot":lineplot, "dataplot":dataplot})

if __name__ == '__main__':
    app.run(debug=True)
