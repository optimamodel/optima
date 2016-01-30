import mpld3
import json
import uuid

from flask import current_app

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with, fields
from flask_restful_swagger import swagger
from flask import helpers

from server.webapp.inputs import SubParser
from server.webapp.dataio import TEMPLATEDIR, upload_dir_user
from server.webapp.utils import load_project, load_progset, load_program, RequestParser, report_exception
from server.webapp.exceptions import ProjectDoesNotExist, ProgsetDoesNotExist, ProgramDoesNotExist
from server.webapp.resources.common import file_resource, file_upload_form_parser

from server.webapp.dbconn import db

from server.webapp.dbmodels import ProgsetsDb, ProgramsDb, ParsetsDb
import optima as op


costcov_parser = RequestParser()
costcov_parser.add_arguments({
    'year': {'required': True, 'type': int, 'location': 'json'}, # 't' for BE
    'spending': {'required': True, 'type': float, 'location': 'json', 'dest': 'cost'},
    'coverage': {'required': True, 'type': float, 'location': 'json', 'dest': 'coverage'},
})

costcov_graph_parser = RequestParser()
costcov_graph_parser.add_arguments({
    't': {'required': True, 'type': int, 'location': 'args'},
    'parset_id': {'required': True, 'type': uuid.UUID, 'location': 'args'}
})

costcov_data_parser = RequestParser()
costcov_data_parser.add_arguments({
    'data': {'type': list, 'location': 'json'},
    'params': {'type': dict, 'location': 'json'}
})

costcov_data_point_parser = RequestParser()
costcov_data_point_parser.add_arguments({
    'year': {'required': True, 'type': int, 'location': 'json'}, # 't' for BE
    'spending': {'required': True, 'type': float, 'location': 'json', 'dest': 'cost'},
    'coverage': {'required': True, 'type': float, 'location': 'json', 'dest': 'coverage'},
})

program_parser = RequestParser()
program_parser.add_arguments({
    'name': {'required': True, 'location': 'json'},
    'short': {'location': 'json'},
    'short_name': {'location': 'json'},
    'category': {'required': True, 'location': 'json'},
    'active': {'type': bool, 'default': False, 'location': 'json'},
    'parameters': {'type': list, 'dest': 'pars', 'location': 'json'},
    'populations': {'type': list, 'location': 'json', 'dest': 'targetpops'},
    'addData': {'type': SubParser(costcov_parser), 'dest': 'costcov', 'action': 'append', 'default': []},
})

query_program_parser = RequestParser()
query_program_parser.add_arguments({
    'name': {'required': True},
    'short': {},
    'short_name': {},
    'category': {'required': True},
    'active': {'type': bool, 'default': False},
    'parameters': {'type': list, 'dest': 'pars', 'location': 'json'},
    'populations': {'type': list, 'dest': 'targetpops', 'location': 'json'},
})

progset_parser = RequestParser()
progset_parser.add_arguments({
    'name': {'required': True},
    'programs': {'required': True, 'type': SubParser(program_parser), 'action': 'append'}
})


class Progsets(Resource):
    """
    Progsets for a given project.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description='Download progsets for the project with the given id.',
        notes="""
            if project exists, returns progsets for it
            if project does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @report_exception
    @marshal_with(ProgsetsDb.resource_fields, envelope='progsets')
    def get(self, project_id):

        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        reply = db.session.query(ProgsetsDb).filter_by(project_id=project_entry.id).all()
        return reply

    @swagger.operation(
        description='Create a progset for the project with the given id.',
        parameters=progset_parser.swagger_parameters()
    )
    @report_exception
    @marshal_with(ProgsetsDb.resource_fields)
    def post(self, project_id):
        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_entry = load_project(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        args = progset_parser.parse_args()

        progset_entry = ProgsetsDb(project_id, args['name'])
        db.session.add(progset_entry)
        db.session.flush()

        progset_entry.create_programs_from_list(args['programs'])

        db.session.commit()

        return progset_entry, 201


class Progset(Resource):
    """
    An individual progset.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description='Download progset with the given id.',
        notes="""
            if progset exists, returns it
            if progset does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @report_exception
    @marshal_with(ProgsetsDb.resource_fields)
    def get(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        progset_entry = load_progset(project_id, progset_id)
        return progset_entry

    @swagger.operation(
        description='Update progset with the given id.',
        notes="""
            if progset exists, returns the updated version
            if progset does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @report_exception
    @marshal_with(ProgsetsDb.resource_fields)
    def put(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))

        progset_entry = load_progset(project_id, progset_id)
        args = progset_parser.parse_args()
        progset_entry.name = args['name']
        db.session.query(ProgramsDb).filter_by(progset_id=progset_entry.id).delete()

        progset_entry.create_programs_from_list(args.get('programs', []))

        db.session.commit()

        return progset_entry

    @swagger.operation(
        description='Delete progset with the given id.',
        notes="""
            if progset exists, deletes it
            if progset does not exist, returns an error.
        """
    )
    @report_exception
    def delete(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        progset_entry = db.session.query(ProgsetsDb).get(progset_id)
        if progset_entry is None:
            raise ProgsetDoesNotExist(id=progset_id)

        if progset_entry.project_id != project_id:
            raise ProgsetDoesNotExist(id=progset_id)

        progset_entry.name
        db.session.query(ProgramsDb).filter_by(progset_id=progset_entry.id).delete()
        db.session.delete(progset_entry)
        db.session.commit()
        return '', 204


class ProgsetData(Resource):

    method_decorators = [report_exception, login_required]

    @swagger.operation(
        produces='application/x-gzip',
        description='Download progset with the given id as Binary.',
        notes="""
            if progset exists, returns it
            if progset does not exist, returns an error.
        """,

    )
    @report_exception
    def get(self, project_id, progset_id):
        current_app.logger.debug("GET /api/project/{}/progsets/{}/data".format(project_id, progset_id))
        progset_entry = load_progset(project_id, progset_id)

        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = progset_entry.as_file(loaddir)

        return helpers.send_from_directory(loaddir, filename)

    @swagger.operation(
        summary='Uploads data for already created progset',
        parameters=file_upload_form_parser.swagger_parameters()
    )
    @report_exception
    @marshal_with(file_resource)
    def post(self, project_id, progset_id, parset_id):
        """
        Uploads Data file, uses it to update the progrset and program models.
        Precondition: model should exist.
        """
        from server.webapp.programs import get_default_programs

        current_app.logger.debug("POST /api/project/{}/progsets/{}/data".format(project_id, progset_id))

        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        source_filename = uploaded_file.source_filename

        progset_entry = load_progset(project_id, progset_id)

        project_entry = load_project(project_id)
        project = project_entry.hydrate()
        if project.data != {}:
            program_list = get_default_programs(project)
        else:
            program_list = []

        from optima.utils import loadobj
        new_progset = loadobj(uploaded_file)
        progset_entry.restore(new_progset, program_list)
        db.session.add(progset_entry)

        db.session.commit()

        reply = {
            'file': source_filename,
            'result': 'Progset %s is updated' % progset_entry.name,
        }
        return reply


class Programs(Resource):
    """
    Programs for a given progset.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description="Get programs for the progset with the given ID.",
        responseClass=ProgramsDb.__name__)
    @marshal_with(ProgramsDb.resource_fields, envelope='programs')
    def get(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s/programs" % (project_id, progset_id))

        progset_entry = load_progset(project_id, progset_id)
        if progset_entry is None:
            raise ProgsetDoesNotExist(id=progset_id)

        reply = db.session.query(ProgramsDb).filter_by(progset_id=progset_entry.id).all()
        return reply

    @swagger.operation(
        description="Create a program for the progset with the given ID.",
        parameters=program_parser.swagger_parameters())
    @marshal_with(ProgramsDb.resource_fields)
    def post(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s/programs" % (project_id, progset_id))

        progset_entry = load_progset(project_id, progset_id)
        if progset_entry is None:
            raise ProgsetDoesNotExist(id=progset_id)

        args = query_program_parser.parse_args()
        args["short"] = args["short_name"]
        del args["short_name"]

        program_entry = ProgramsDb(project_id, progset_id, **args)
        db.session.add(program_entry)
        db.session.flush()
        db.session.commit()

        return program_entry, 201


class CostCoverage(Resource):
    """
    Costcoverage for a given Program.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description="Get costcoverage parameters and data for the given program.")
    def get(self, project_id, progset_id, program_id):

        program_entry = load_program(project_id, progset_id, program_id)

        return {"params": program_entry.ccopars or {},
                "data": program_entry.data_db_to_api()}

    @swagger.operation(
        description="Replace costcoverage parameters and data for the given program.")
    def put(self, project_id, progset_id, program_id):

        program_entry = load_program(project_id, progset_id, program_id)

        args = costcov_data_parser.parse_args()
        program_entry.ccopars = args.get('params', {})
        program_entry.costcov = program_entry.data_api_to_db(args.get('data', []))

        db.session.flush()
        db.session.commit()

        return {"params": program_entry.ccopars or {},
                "data": program_entry.data_db_to_api()}


class CostCoverageGraph(Resource):
    """
    Costcoverage graph for a Program.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description="Get graph.")
    def get(self, project_id, progset_id, program_id):
        """
        parameters:
        t = year ( should be >= startyear in data)
        parset_id - ID of the parset (one of the project parsets - not related to program parameters)
        """
        args = costcov_graph_parser.parse_args()
        print "args", args
        parset_id = args['parset_id']
        t = args['t']

        program_entry = load_program(project_id, progset_id, program_id)
        if program_entry is None:
            raise ProgramDoesNotExist(id=program_id, project_id=project_id)
        program_instance = program_entry.hydrate()
        parset_entry = db.session.query(ParsetsDb).filter_by(id=parset_id, project_id=project_id).first()
        if parset_entry is None:
            raise ParsetDoesNotExist(id=parset_id, project_id=project_id)
        parset_instance = parset_entry.hydrate()

        plot = program_instance.plotcoverage(t=t, parset=parset_instance)

        mpld3.plugins.connect(plot, mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))
        # a hack to get rid of NaNs, javascript JSON parser doesn't like them
        json_string = json.dumps(mpld3.fig_to_dict(plot)).replace('NaN', 'null')
        return json.loads(json_string)


class CostCoverageData(Resource):
    """
    Modification of data points for the given program.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(description="Add new data point.",
        parameters=costcov_data_point_parser.swagger_parameters())
    def post(self, project_id, progset_id, program_id):
        """
        adds a _new_ data point to program parameters.
        It should then be given to BE in this way:
        program.addcostcovdatum({
            t=<args.year>,
            cost=<args.cost>,
            coverage=<args.coverage>
            })
        """
        args = costcov_data_point_parser.parse_args()

        program_entry = load_program(project_id, progset_id, program_id)
        if program_entry is None:
            raise ProgramDoesNotExist(id=program_id, project_id=project_id)
        program_instance = program_entry.hydrate()
        program_instance.addcostcovdatum({'t': args['year'], 'cost': args['cost'], 'coverage': args['coverage']})
        program_entry.restore(program_instance)
        result = {"params": program_entry.ccopars or {},
                "data": program_entry.data_db_to_api()}
        db.session.add(program_entry)
        db.session.commit()

        return result, 201

    @swagger.operation(description="Edit existing data point.",
        parameters=costcov_data_point_parser.swagger_parameters())
    def put(self, project_id, progset_id, program_id):
        """
        edits existing data point to program parameters.
        It should then be given to BE in this way:
        program.addcostcovdatum({
            t=<args.year>,
            cost=<args.cost>,
            coverage=<args.coverage>
            })
        """
        args = costcov_data_point_parser.parse_args()
        print "args", args
        program_entry = load_program(project_id, progset_id, program_id)
        if program_entry is None:
            raise ProgramDoesNotExist(id=program_id, project_id=project_id)
        program_instance = program_entry.hydrate()
        program_instance.addcostcovdatum({'t': args['year'], 'cost': args['cost'], 'coverage': args['coverage']}, overwrite = True)
        program_entry.restore(program_instance)
        result = {"params": program_entry.ccopars or {},
                "data": program_entry.data_db_to_api()}
        db.session.add(program_entry)
        db.session.commit()

        return result, 201        