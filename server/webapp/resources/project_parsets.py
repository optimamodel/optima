from flask import current_app

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, abort
from flask_restful_swagger import swagger

from server.webapp.inputs import SubParser
from server.webapp.utils import load_project, RequestParser
from server.webapp.exceptions import ParsetDoesNotExist

from server.webapp.dbconn import db
from server.webapp.dbmodels import ParsetsDb
from server.webapp.fields import Json, Uuid

import optima as op


class Parsets(Resource):
    """
    Parsets for a given project.
    """
    class_decorators = [login_required]

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
    class_decorators = [login_required]

    @swagger.operation(
        description='Delete parset with the given id.',
        notes="""
            if parset exists, delete it
            if parset does not exist, returns an error.
        """
    )
    def delete(self, project_id, parset_id):  # TODO: we don't need project_id, because parset_id uniquely identifies the resourse

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
    "graphs": Json
}


class ParsetsCalibration(Resource):
    """
    Calibration info for the Parset.
    """

    class_decorators = [login_required]

    @swagger.operation(
        description='Provides calibration information for the given parset',
        notes="""
        Returns data suitable for manual calibration and the set of corresponding graphs.
        """
    )
    @marshal_with(calibration_fields, envelope="calibration")
    def get(self, parset_id):
        import mpld3
        import json
        current_app.logger.debug("/api/parsets/{}/calibration/manual".format(parset_id))

        parset = db.session.query(ParsetsDb).filter_by(id=parset_id).first()
        if parset is None:
            raise ParsetDoesNotExist(id=parset_id)

        # get manual parameters
        parset_instance = parset.hydrate()
        mflists = parset_instance.manualfitlists()
        parameters = [{"key": key, "label": label, "subkey": subkey, "value": value, "type": ptype}
                      for (key, label, subkey, value, ptype) in
                      zip(mflists['keys'], mflists['labels'], mflists['subkeys'], mflists['values'], mflists['types'])]
        # REMARK: this returns the dictionary of lists to be compatible with how Cliff uses it in gui.py
        # but I suggest we convert this into per-variable dictionary (TODO)

        project_entry = load_project(parset.project_id, raise_exception=True)
        project_instance = project_entry.hydrate()
        simparslist = parset_instance.interp()
        results = project_instance.runsim(simpars=simparslist)  # TODO: read from DB ?
        graphs = op.epiplot(results, figsize=(3,2))

        jsons = []
        # TODO: refactor this?
        for graph in graphs:
            # Add necessary plugins here
            mpld3.plugins.connect(graphs[graph], mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))
            json_string = json.dumps(mpld3.fig_to_dict(graphs[graph])).replace('NaN','null')
            jsons.append(json.loads(json_string))

        return {
            "parset_id": parset_id,
            "parameters": parameters,
            "graphs": jsons
        }
