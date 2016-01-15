from datetime import datetime
import dateutil

from flask import current_app, helpers

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, abort
from flask_restful_swagger import swagger

from server.webapp.inputs import SubParser
from server.webapp.utils import load_project, RequestParser, report_exception, TEMPLATEDIR, upload_dir_user
from server.webapp.exceptions import ParsetDoesNotExist

from server.webapp.dbconn import db
from server.webapp.dbmodels import ParsetsDb, ResultsDb
from server.webapp.fields import Json, Uuid

import optima as op


class Parsets(Resource):
    """
    Parsets for a given project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description='Download parsets for the project with the given id.',
        notes="""
            if project exists, returns parsets for it
            if project does not exist, returns an error.
        """,
        responseClass=ParsetsDb.__name__
    )
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def get(self, project_id):

        current_app.logger.debug("/api/project/%s/parsets" % str(project_id))
        project_entry = load_project(project_id, raise_exception=True)

        reply = db.session.query(ParsetsDb).filter_by(project_id=project_entry.id).all()
        return [item.hydrate() for item in reply]  # TODO: project_id should be not null


class ParsetsDetail(Resource):
    """
    Single Parset.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description='Delete parset with the given id.',
        notes="""
            if parset exists, delete it
            if parset does not exist, returns an error.
        """
    )
    def delete(self, project_id, parset_id):

        current_app.logger.debug("/api/project/{}/parsets/{}".format(project_id, parset_id))
        project_entry = load_project(project_id, raise_exception=True)

        parset = db.session.query(ParsetsDb).filter_by(project_id=project_entry.id, id=parset_id).first()
        if parset is None:
            raise ParsetDoesNotExist(id=parset_id)

        # Is this how we should check for default parset?
        if parset.name == 'Default':  # TODO: it is lowercase
            abort(403)

        # TODO: also delete the corresponding calibration results
        db.session.query(ParsetsDb).filter_by(id=parset_id).delete()
        db.session.commit()

        return '', 204


calibration_fields = {
    "parset_id": Uuid,
    "parameters": Json,
    "graphs": Json,
    "selectors": Json
}

calibration_parser = RequestParser()
calibration_parser.add_argument('which', location='args', default=None, action='append')


calibration_update_parser = RequestParser()
calibration_update_parser.add_arguments({
    'which': {'default': None, 'action': 'append'},
    'parameters': {'required': True, 'type': dict, 'action': 'append'},
    'doSave': {'default': False, 'type': bool, 'location': 'args'},
})


class ParsetsCalibration(Resource):
    """
    Calibration info for the Parset.
    """

    method_decorators = [report_exception, login_required]

    def _result_to_jsons(self, result, which):
        import mpld3
        import json
        graphs = op.epiplot(result, figsize=(4, 3), which = which)  # TODO: store if that becomes an efficiency issue
        jsons = []
        for graph in graphs:
            # Add necessary plugins here
            mpld3.plugins.connect(graphs[graph], mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))
            # a hack to get rid of NaNs, javascript JSON parser doesn't like them
            json_string = json.dumps(mpld3.fig_to_dict(graphs[graph])).replace('NaN', 'null')
            jsons.append(json.loads(json_string))
        return jsons

    def _selectors_from_result(self, result, which):
        graph_selectors = result.make_graph_selectors(which)
        keys = graph_selectors['keys']
        names = graph_selectors['names']
        checks = graph_selectors['checks']
        selectors = [{'key': key, 'name': name, 'checked': checked}
                     for (key, name, checked) in zip(keys, names, checks)]
        return selectors

    def _which_from_selectors(self, graph_selectors):
        return [item['key'] for item in graph_selectors if item['checked']]

    @swagger.operation(
        description='Provides calibration information for the given parset',
        notes="""
        Returns data suitable for manual calibration and the set of corresponding graphs.
        """,
        parameters=calibration_parser.swagger_parameters()
    )
    @marshal_with(calibration_fields, envelope="calibration")
    def get(self, parset_id):
        current_app.logger.debug("/api/parsets/{}/calibration".format(parset_id))
        args = calibration_parser.parse_args()
        which = args.get('which')

        parset_entry = db.session.query(ParsetsDb).filter_by(id=parset_id).first()
        if parset_entry is None:
            raise ParsetDoesNotExist(id=parset_id)

        # get manual parameters
        parset_instance = parset_entry.hydrate()
        mflists = parset_instance.manualfitlists()
        parameters = [{"key": key, "label": label, "subkey": subkey, "value": value, "type": ptype}
                      for (key, label, subkey, value, ptype) in
                      zip(mflists['keys'], mflists['labels'], mflists['subkeys'], mflists['values'], mflists['types'])]
        # REMARK: manualfitlists() in parset returns the lists compatible with usage on BE,
        # but for FE we prefer list of dicts

        project_entry = load_project(parset_entry.project_id, raise_exception=True)
        project_instance = project_entry.hydrate()
        result_entry = [item for item in project_entry.results if
                        item.parset_id == parset_id and item.calculation_type == ResultsDb.CALIBRATION_TYPE]
        if result_entry:
            result = result_entry[0].hydrate()
        else:
            simparslist = parset_instance.interp()
            result = project_instance.runsim(simpars=simparslist)

        selectors = self._selectors_from_result(result, which)
        which = which or self._which_from_selectors(selectors)
        graphs = self._result_to_jsons(result, which)

        return {
            "parset_id": parset_id,
            "parameters": parameters,
            "graphs": graphs,
            "selectors": selectors
        }

    @marshal_with(calibration_fields, envelope="calibration")
    def put(self, parset_id):
        current_app.logger.debug("PUT /api/parsets/{}/calibration".format(parset_id))
        args = calibration_update_parser.parse_args()
        parameters = args.get('parameters', [])
        which = args.get('which')
        doSave = args.get('doSave')
        # TODO save if doSave=true

        parset_entry = db.session.query(ParsetsDb).filter_by(id=parset_id).first()
        if parset_entry is None:
            raise ParsetDoesNotExist(id=parset_id)

        # get manual parameters
        parset_instance = parset_entry.hydrate()
        mflists = {'keys': [], 'subkeys': [], 'types': [], 'values': [], 'labels': []}
        for param in parameters:
            mflists['keys'].append(param['key'])
            mflists['subkeys'].append(param['subkey'])
            mflists['types'].append(param['type'])
            mflists['labels'].append(param['label'])
            mflists['values'].append(param['value'])
        parset_instance.update(mflists)
        # recalculate
        project_entry = load_project(parset_entry.project_id, raise_exception=True)
        project_instance = project_entry.hydrate()
        simparslist = parset_instance.interp()
        result = project_instance.runsim(simpars=simparslist)

        if doSave:  # save the updated results
            parset_entry.pars = op.saves(parset_instance.pars)
            parset_entry.updated = datetime.now(dateutil.tz.tzutc())
            db.session.add(parset_entry)
            result_entry = [item for item in project_entry.results if
                            item.parset_id == parset_id and item.calculation_type == ResultsDb.CALIBRATION_TYPE]
            if result_entry:
                result_entry = result_entry[0]
                result_entry.blob = op.saves(result)
            else:
                result_entry = ResultsDb(
                    parset_id=parset_id,
                    project_id=project_entry.id,
                    calculation_type=ResultsDb.CALIBRATION_TYPE,
                    blob=op.saves(result)
                )
            db.session.add(result_entry)
            db.session.commit()

        selectors = self._selectors_from_result(result, which)
        which = which or self._which_from_selectors(selectors)
        graphs = self._result_to_jsons(result, which)

        return {
            "parset_id": parset_id,
            "parameters": args['parameters'],
            "graphs": graphs,
            "selectors": selectors
        }


class ParsetsData(Resource):
    """
    Export and import of the existing parset in / from pickled format.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        produces='application/x-gzip',
        summary='Download data for the parset with the given id from project with the given id',
        notes="""
        if parset exists, returns data for it
        if parset does not exist, returns an error.
        """
    )
    def get(self, project_id, parset_id):
        current_app.logger.debug("/api/project/{0}/parset/{1}/data".format(project_id, parset_id))
        parset_entry = db.session.query(ParsetsDb).filter_by(id=parset_id, project_id=project_id).first()

        # return result as a file
        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = parset_entry.as_file(loaddir)
        # TODO: add filename to the response and add parset_id to filename

        return helpers.send_from_directory(loaddir, filename)
