from datetime import datetime
import dateutil
import uuid

from flask import current_app, helpers, make_response, request

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, abort
from flask_restful_swagger import swagger

from server.webapp.inputs import SubParser, secure_filename_input, AllowedSafeFilenameStorage

from server.webapp.utils import (load_project, RequestParser, report_exception, TEMPLATEDIR,
                                 upload_dir_user, save_result)
from server.webapp.exceptions import ParsetDoesNotExist, ParsetAlreadyExists

from server.webapp.dbconn import db
from server.webapp.dbmodels import ParsetsDb, ResultsDb
from server.webapp.fields import Json, Uuid

import optima as op


copy_parser = RequestParser()
copy_parser.add_arguments({
    'name': {'required': True},
    'parset_id': {'type': uuid.UUID}
})


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
    @report_exception
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def get(self, project_id):

        current_app.logger.debug("/api/project/%s/parsets" % str(project_id))
        project_entry = load_project(project_id, raise_exception=True)

        reply = db.session.query(ParsetsDb).filter_by(project_id=project_entry.id).all()
        return [item.hydrate() for item in reply]  # TODO: project_id should be not null

    @swagger.operation(
        description='Create new parset with default settings or copy existing parset',
        notes="""
            If parset_id argument is given, copy from the existing parset.
            Otherwise, create a parset with default settings
            """
    )
    @report_exception
    def post(self, project_id):
        current_app.logger.debug("POST /api/project/{}/parsets".format(project_id))
        args = copy_parser.parse_args()
        print "args", args
        name = args['name']
        parset_id = args.get('parset_id')

        project_entry = load_project(project_id, raise_exception=True)
        project_instance = project_entry.hydrate()
        if name in project_instance.parsets:
            raise ParsetAlreadyExists(project_id, name)
        if not parset_id:
            # create new parset with default settings
            project_instance.ensureparset(name)
            new_result = project_instance.runsim(name)
            project_entry.restore(project_instance)
            db.session.add(project_entry)

            result_record = save_result(project_entry.id, new_result, name)
            db.session.add(result_record)
        else:
            # dealing with uid's directly might be messy...
            original_parset = [item for item in project_entry.parsets if item.id == parset_id]
            if not original_parset:
                raise ParsetDoesNotExist(parset_id, project_id=project_id)
            original_parset = original_parset[0]
            parset_name = original_parset.name
            project_instance.copyparset(orig=parset_name, new=name)
            project_entry.restore(project_instance)
            db.session.add(project_entry)

            old_result_record = db.session.query(ResultsDb).filter_by(
                parset_id=str(parset_id), project_id=str(project_id),
                calculation_type=ResultsDb.CALIBRATION_TYPE).first()
            old_result = old_result_record.hydrate()
            new_result = op.dcp(old_result)
            new_result_record = save_result(project_entry.id, new_result, name)
            db.session.add(new_result_record)

        db.session.commit()

        rv = []
        for item in project_entry.parsets:
            rv_item = item.hydrate().__dict__
            rv_item['id'] = item.id
            rv.append(rv_item)

        return rv


rename_parser = RequestParser()
rename_parser.add_argument('name', required=True)


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
    @report_exception
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def delete(self, project_id, parset_id):

        current_app.logger.debug("DELETE /api/project/{}/parsets/{}".format(project_id, parset_id))
        project_entry = load_project(project_id, raise_exception=True)

        parset = db.session.query(ParsetsDb).filter_by(project_id=project_entry.id, id=parset_id).first()
        if parset is None:
            raise ParsetDoesNotExist(id=parset_id, project_id=project_id)

        # Is this how we should check for default parset?
        if parset.name.lower() == 'default':  # TODO: it is lowercase
            abort(403)

        # TODO: also delete the corresponding calibration results
        db.session.query(ResultsDb).filter_by(id=parset_id, calculation_type=ResultsDb.CALIBRATION_TYPE).delete()
        db.session.query(ParsetsDb).filter_by(id=parset_id).delete()
        db.session.commit()

        return '', 204

    @swagger.operation(
        description='Rename parset with the given id',
        notes="""
            if parset exists, rename it
            if parset does not exist, return an error.
            """
    )
    @report_exception
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def put(self, project_id, parset_id):
        """
        For consistency, let's always return the updated parsets for operations on parsets
        (so that FE doesn't need to perform another GET call)
        """

        current_app.logger.debug("PUT /api/project/{}/parsets/{}".format(project_id, parset_id))
        args = rename_parser.parse_args()
        name = args['name']

        project_entry = load_project(project_id, raise_exception=True)
        target_parset = [item for item in project_entry.parsets if item.id == parset_id]
        if target_parset:
            target_parset = target_parset[0]
        if not target_parset:
            raise ParsetDoesNotExist(id=parset_id, project_id=project_id)
        target_parset.name = name
        db.session.add(target_parset)
        db.session.commit()
        return [item.hydrate() for item in project_entry.parsets]


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
        graphs = op.plotting.makeplots(result, figsize=(4, 3), toplot=[str(w) for w in which])  # TODO: store if that becomes an efficiency issue
        jsons = []
        for graph in graphs:
            # Add necessary plugins here
            mpld3.plugins.connect(graphs[graph], mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))
            # a hack to get rid of NaNs, javascript JSON parser doesn't like them
            json_string = json.dumps(mpld3.fig_to_dict(graphs[graph])).replace('NaN', 'null')
            jsons.append(json.loads(json_string))
        return jsons

    def _selectors_from_result(self, result, which):
        graph_selectors = op.getplotselections(result)
        keys = graph_selectors['keys']
        names = graph_selectors['names']
        if which is None:
            checks = graph_selectors['defaults']
        else:
            checks = [key in which for key in keys]
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
    @report_exception
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

    @report_exception
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


manual_calibration_parser = RequestParser()
manual_calibration_parser.add_argument('maxtime', required=False, default=60)


class ParsetsAutomaticCalibration(Resource):

    @swagger.operation(
        summary='Launch manual calibration for the selected parset',
        parameters=manual_calibration_parser.swagger_parameters()
    )
    def post(self, parset_id):
        from server.webapp.utils import load_project
        from server.webapp.tasks import run_autofit
        from server.webapp.dbmodels import ParsetsDb

        args = manual_calibration_parser.parse_args()

        # FixMe: use load_parset once the branch having it is merged
        parset_entry = ParsetsDb.query.get(parset_id)

        project_entry = load_project(parset_entry.project_id, raise_exception=True)

        project_be = project_entry.hydrate()

        run_autofit.delay(project_be, parset_entry.name, args['maxtime'])

        return '', 201


file_upload_form_parser = RequestParser()
file_upload_form_parser.add_argument('file', type=AllowedSafeFilenameStorage, location='files', required=True)


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
    @report_exception
    def get(self, project_id, parset_id):
        current_app.logger.debug("GET /api/project/{0}/parset/{1}/data".format(project_id, parset_id))
        parset_entry = db.session.query(ParsetsDb).filter_by(id=parset_id, project_id=project_id).first()
        if parset_entry is None:
            raise ParsetDoesNotExist(id=parset_id, project_id=project_id)

        # return result as a file
        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = parset_entry.as_file(loaddir)

        response = helpers.send_from_directory(loaddir, filename)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)

        return response

    @swagger.operation(
        summary='Upload data for the parset with the given id in project with the given id',
        notes="""
        if parset exists, updates it with data from the file
        if parset does not exist, returns an error"""
    )
    @report_exception
    @marshal_with(ParsetsDb.resource_fields, envelope='parsets')
    def post(self, project_id, parset_id):
        # TODO replace this with app.config
        current_app.logger.debug("POST /api/project/{0}/parset/{1}/data".format(project_id, parset_id))

        print request.files, request.args
        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        project_entry = load_project(project_id, raise_exception=True)

        parset_entry = project_entry.find_parset(parset_id)
        parset_instance = op.loadobj(uploaded_file)

        parset_entry.restore(parset_instance)
        db.session.add(parset_entry)
        db.session.flush()

        # recalculate data (TODO: verify with Robyn if it's needed )
        project_instance = project_entry.hydrate()
        result = project_instance.runsim(parset_entry.name)
        current_app.logger.info("runsim result for project %s: %s" % (project_id, result))

        db.session.add(project_entry)  # todo: do we need to log that project was updated?
        db.session.flush()

        result_record = save_result(project_entry.id, result, parset_entry.name)
        db.session.add(result_record)

        db.session.commit()

        return [item.hydrate() for item in project_entry.parsets]
