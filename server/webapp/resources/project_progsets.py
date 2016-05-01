import mpld3
import json
from pprint import pprint
import pprint

from flask import current_app

from flask.ext.login import login_required
from flask_restful import Resource, marshal_with
from flask_restful_swagger import swagger
from flask import helpers

from server.webapp.dataio import TEMPLATEDIR, upload_dir_user
from server.webapp.utils import load_project_record, load_progset_record, report_exception, modify_program_record, load_program_record
from server.webapp.exceptions import ProjectDoesNotExist, ProgsetDoesNotExist, ProgramDoesNotExist, ParsetDoesNotExist
from server.webapp.resources.common import file_resource, file_upload_form_parser

from server.webapp.dbconn import db

from server.webapp.dbmodels import ProgsetsDb, ProgramsDb, ParsetsDb, ResultsDb

from server.webapp.serializers.project_progsets import (progset_parser, param_fields,
    effect_parser, progset_effects_fields, program_parser, query_program_parser,
    costcov_graph_parser, costcov_data_point_parser,
    costcov_data_locator_parser, costcov_param_parser)

from server.webapp.jsonhelper import normalize_obj

import uuid
from flask_restful import fields
from server.webapp.utils import RequestParser
from server.webapp.inputs import SubParser, Json as JsonInput
from server.webapp.fields import Json, Uuid



def load_program(project_id, progset_id, program_id):
    program_entry = load_program_record(project_id, progset_id, program_id)
    if program_entry is None:
        raise ProgramDoesNotExist(id=program_id, project_id=project_id)
    return program_entry.hydrate()


def load_parset(project_id, parset_id):
    parset_entry = db.session.query(ParsetsDb).filter_by(
        id=parset_id, project_id=project_id).first()
    if parset_entry is None:
        raise ParsetDoesNotExist(id=parset_id, project_id=project_id)
    return parset_entry.hydrate()


def load_result(project_id, parset_id):
    result_entry = db.session.query(ResultsDb).filter_by(
        project_id=project_id, parset_id=parset_id,
        calculation_type=ResultsDb.CALIBRATION_TYPE).first()
    # TODO custom exception
    if result_entry is None:
        raise Exception
    return result_entry.hydrate()


def print_parset(parset):
    result = {
        'popkeys': normalize_obj(parset.popkeys),
        'uid': str(parset.uid),
        'name': parset.name,
        'project_id': parset.project.id if parset.project else '',
    }
    s = pprint.pformat(result, indent=1) + "\n"
    for pars in parset.pars:
        for key, par in pars.items():
            if hasattr(par, 'y'):
                par = normalize_obj(par.y)
            elif hasattr(par, 'p'):
                par = normalize_obj(par.p)
            else:
                par = normalize_obj(par)
            s += pprint.pformat({ key: par }) + "\n"
    return s



def promotetoarray(x):
    ''' Small function to ensure consistent format for things that should be arrays '''
    from numbers import Number
    from numpy import ndarray
    if isinstance(x, Number):
        return [x]
    elif isinstance(x, list):
        return x
    elif isinstance(x, ndarray):
        return x.tolist()
    else:
        raise Exception("Expecting a list/number; got: %s" % str(x))



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
    @marshal_with(ProgsetsDb.resource_fields, envelope='progsets')
    def get(self, project_id):

        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_record = load_project_record(project_id)
        if project_record is None:
            raise ProjectDoesNotExist(id=project_id)

        progsets_record = db.session.query(ProgsetsDb).filter_by(project_id=project_record.id).all()
        for progset_record in progsets_record:
            progset_record.get_extra_data()
            for program_record in progset_record.programs:
                program_record.get_optimizable()

        return progsets_record

    @swagger.operation(
        description='Create a progset for the project with the given id.',
        parameters=progset_parser.swagger_parameters()
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def post(self, project_id):
        current_app.logger.debug("/api/project/%s/progsets" % project_id)
        project_entry = load_project_record(project_id)
        if project_entry is None:
            raise ProjectDoesNotExist(id=project_id)

        args = progset_parser.parse_args()

        progset_entry = ProgsetsDb(project_id, args['name'])
        db.session.add(progset_entry)
        db.session.flush()

        progset_entry.recreate_programs_from_list(args['programs'], progset_entry.id)

        db.session.commit()

        progset_entry.get_extra_data()

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
    @marshal_with(ProgsetsDb.resource_fields)
    def get(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))
        progset_entry = load_progset_record(project_id, progset_id)

        progset_entry.get_extra_data()

        return progset_entry

    @swagger.operation(
        description='Update progset with the given id.',
        notes="""
            if progset exists, returns the updated version
            if progset does not exist, returns an error.
        """,
        responseClass=ProgsetsDb.__name__
    )
    @marshal_with(ProgsetsDb.resource_fields)
    def put(self, project_id, progset_id):
        current_app.logger.debug("/api/project/%s/progsets/%s" % (project_id, progset_id))

        progset_entry = load_progset_record(project_id, progset_id)
        args = progset_parser.parse_args()
        progset_entry.name = args['name']
        progset_entry.recreate_programs_from_list(args.get('programs', []), progset_id)

        db.session.commit()

        progset_entry.get_extra_data()

        return progset_entry

    @swagger.operation(
        description='Delete progset with the given id.',
        notes="""
            if progset exists, deletes it
            if progset does not exist, returns an error.
        """
    )
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
    def get(self, project_id, progset_id):
        current_app.logger.debug("GET /api/project/{}/progsets/{}/data".format(project_id, progset_id))
        progset_entry = load_progset_record(project_id, progset_id)

        loaddir = upload_dir_user(TEMPLATEDIR)
        if not loaddir:
            loaddir = TEMPLATEDIR

        filename = progset_entry.as_file(loaddir)

        return helpers.send_from_directory(loaddir, filename)

    @swagger.operation(
        summary='Uploads data for already created progset',
        parameters=file_upload_form_parser.swagger_parameters()
    )
    @marshal_with(file_resource)
    def post(self, project_id, progset_id):
        """
        Uploads Data file, uses it to update the progrset and program models.
        Precondition: model should exist.
        """
        from server.webapp.parser import get_default_program_summaries

        current_app.logger.debug("POST /api/project/{}/progsets/{}/data".format(project_id, progset_id))

        args = file_upload_form_parser.parse_args()
        uploaded_file = args['file']

        source_filename = uploaded_file.source_filename

        progset_entry = load_progset_record(project_id, progset_id)

        project_entry = load_project_record(project_id)
        project = project_entry.hydrate()
        if project.data != {}:
            program_list = get_default_program_summaries(project)
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


class ProgsetParams(Resource):

    @swagger.operation(
        description='Get param/populations sets for the selected progset'
    )
    @marshal_with(param_fields)
    def get(self, project_id, progset_id, parset_id):
        from server.webapp.utils import load_progset_record, load_parset_record

        progset_entry = load_progset_record(project_id, progset_id)
        progset_be = progset_entry.hydrate()

        parset_entry = load_parset_record(project_id, parset_id)
        parset_be = parset_entry.hydrate()

        param_names = set([p['param'] for p in progset_be.targetpars])
        params = [{
            'name': name,
            'populations': [{
                'pop': pop,
                'programs': [{
                    'name': program.name,
                    'short_name': program.short,
                } for program in progs]
            } for pop, progs in progset_be.progs_by_targetpar(name).iteritems()],
            'coverage': parset_be.pars[0][name].coverage,
            'proginteract': parset_be.pars[0][name].proginteract
        } for name in param_names]

        return params


class ProgsetEffects(Resource):

    method_decorators = [report_exception, login_required]

    @swagger.operation(
        summary='Get List of existing Progset effects for the selected progset'
    )
    @marshal_with(progset_effects_fields)
    def get(self, project_id, progset_id):
        from server.webapp.utils import load_progset_record

        progset_entry = load_progset_record(project_id, progset_id)
        return progset_entry

    @swagger.operation(
        summary='Saves a list of Progset effects for the selected progset',
        parameters=effect_parser.swagger_parameters()
    )
    @marshal_with(progset_effects_fields)
    def put(self, project_id, progset_id):
        from server.webapp.utils import load_progset_record

        progset_entry = load_progset_record(project_id, progset_id)

        args = effect_parser.parse_args()
        progset_entry.effects = args.get('effects', [])

        db.session.add(progset_entry)
        db.session.commit()

        return progset_entry


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

        progset_entry = load_progset_record(project_id, progset_id)
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

        progset_entry = load_progset_record(project_id, progset_id)
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



popsize_parser = RequestParser()
popsize_parser.add_arguments(
    {'parset_id': {'required': True, 'type': uuid.UUID, 'location': 'args'},})

class PopSize(Resource):
    """
    Estimated popsize for the given Program.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description="Calculate popsize for the given program and parset(result).",
        parameters=popsize_parser.swagger_parameters())
    def get(self, project_id, progset_id, program_id):
        current_app.logger.debug(
            "/api/project/%s/progsets/%s/programs/%s/popsize" %
            (project_id, progset_id, program_id))
        parset_id = popsize_parser.parse_args()['parset_id']
        program = load_program(project_id, progset_id, program_id)
        if not program.targetpops:
            program.targetpops = ['tot']
        parset = load_parset(project_id, parset_id)
        result = load_result(project_id, parset_id)
        years = range(int(result.settings.start), int(result.settings.end + 1))
        popsizes = program.gettargetpopsize(t=years, parset=parset, results=result)
        popsizes = promotetoarray(popsizes)
        result = {
            'popsizes': [
                { 'year': year, 'popsize': popsize }
                for (year, popsize) in zip(years, popsizes) ]
          }
        # current_app.logger.debug("payload = \n%s\n" % pprint.pformat(result, indent=1))
        return result


costcov_data_parser.add_arguments({
    'data': {'type': list, 'location': 'json'},
    'params': {'type': dict, 'location': 'json'}
})

class CostCoverage(Resource):
    """
    Costcoverage for a given Program.
    """
    method_decorators = [report_exception, login_required]

    @swagger.operation(
        description="Get costcoverage parameters and data for the given program.")
    def get(self, project_id, progset_id, program_id):

        program_entry = load_program_record(project_id, progset_id, program_id)

        return {"params": program_entry.ccopars or {},
                "data": program_entry.data_db_to_api()}

    @swagger.operation(
        description="Replace costcoverage parameters and data for the given program.")
    def put(self, project_id, progset_id, program_id):

        program_entry = load_program_record(project_id, progset_id, program_id)

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

    @swagger.operation(description="Get graph.",
                       parameters=costcov_graph_parser.swagger_parameters())
    def get(self, project_id, progset_id, program_id):
        """
        parameters:
        t = year, or comma-separated list of years (should be >= startyear in data)
        parset_id - ID of the parset (one of the project parsets - not related to program parameters)
        """
        args = costcov_graph_parser.parse_args()
        parset_id = args['parset_id']

        try:
            t = [int(x) for x in args['t'].split(',')]
        except ValueError:
            raise ValueError("t must be a year or a comma-separated list of years.")

        plotoptions = {}
        for x in ['caption', 'xupperlim', 'perperson']:
            if args.get(x):
                plotoptions[x] = args[x]

        program = load_program(project_id, progset_id, program_id)
        parset = load_parset(project_id, parset_id)

        plot = program.plotcoverage(t=t, parset=parset, plotoptions=plotoptions)

        mpld3.plugins.connect(plot, mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))
        # a hack to get rid of NaNs, javascript JSON parser doesn't like them
        json_string = json.dumps(mpld3.fig_to_dict(plot)).replace('NaN', 'null').replace('None', '')
        return json.loads(json_string)


class CostCoverageData(Resource):
    """
    Modification of data points for the given program.
    """
    method_decorators = [report_exception, login_required]

    def add_data_for_instance(self, program_instance, args, overwrite=False):
        program_instance.addcostcovdatum(
            {'t': args['year'], 'cost': args['cost'], 'coverage': args['coverage']},
            overwrite=overwrite)

    def update_data_for_instance(self, program_instance, args):
        self.add_data_for_instance(program_instance, args, overwrite=True)

    def delete_data_for_instance(self, program_instance, args):
        program_instance.rmcostcovdatum(year=args['year'])

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
        result = modify_program_record(project_id, progset_id, program_id, args, self.add_data_for_instance)

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
        result = modify_program_record(project_id, progset_id, program_id, args, self.update_data_for_instance)

        return result

    @swagger.operation(description="Remove a data point.",
                       parameters=costcov_data_locator_parser.swagger_parameters())
    def delete(self, project_id, progset_id, program_id):
        """
        removes data point for the given year from program parameters.
        """
        args = costcov_data_locator_parser.parse_args()
        result = modify_program_record(project_id, progset_id, program_id, args, self.delete_data_for_instance)

        return result


class CostCoverageParam(Resource):
    """
    Modification of parameters for the given program.
    """
    method_decorators = [report_exception, login_required]

    def add_param_for_instance(self, program_instance, args, overwrite=False):
        program_instance.costcovfn.addccopar(
            {
                'saturation': (args['saturation_lower'], args['saturation_upper']),
                't': args['year'],
                'unitcost': (args['unitcost_lower'], args['unitcost_upper'])
            },
            overwrite=overwrite)

    def update_param_for_instance(self, program_instance, args):
        self.add_param_for_instance(program_instance, args, overwrite=True)

    def delete_param_for_instance(self, program_instance, args):
        program_instance.costcovfn.rmccopar(t=args['year'])

    @swagger.operation(description="Add new cco parameter.",
                       parameters=costcov_param_parser.swagger_parameters())
    def post(self, project_id, progset_id, program_id):
        """
        adds a _new_ cco param to program parameters.
        It should then be given to BE in this way:
        program.addccopar({
            'saturation': (saturationpercent_lower,saturationpercent_upper),
            't': year,
            'unitcost': (unitcost_lower,unitcost_upper)})
        """
        args = costcov_param_parser.parse_args()
        result = modify_program_record(project_id, progset_id, program_id, args, self.add_param_for_instance)


        return result, 201

    @swagger.operation(description="Edit existing cco parameter.",
                       parameters=costcov_param_parser.swagger_parameters())
    def put(self, project_id, progset_id, program_id):
        """
        edits existing data point to program parameters.
        It should then be given to BE in this way:
        program.addccopar({
            'saturation': (saturationpercent_lower,saturationpercent_upper),
            't': year,
            'unitcost': (unitcost_lower,unitcost_upper)})
        """
        args = costcov_param_parser.parse_args()
        result = modify_program_record(project_id, progset_id, program_id, args, self.update_param_for_instance)

        return result

    @swagger.operation(description="Remove cco parameter.",
                       parameters=costcov_data_locator_parser.swagger_parameters())
    def delete(self, project_id, progset_id, program_id):
        """
        removes cco parameter for the given year from program parameters.
        """
        args = costcov_data_locator_parser.parse_args()
        result = modify_program_record(project_id, progset_id, program_id, args, self.delete_param_for_instance)

        return result
