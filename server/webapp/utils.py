import os
from collections import OrderedDict

import flask.json
import numpy as np

from flask import current_app
from flask.ext.restful.reqparse import RequestParser as OrigReqParser
from validate_email import validate_email
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

import optima as op


ALLOWED_EXTENSIONS = {'txt', 'xlsx', 'xls', 'json', 'prj', 'prg', 'par'}


def allowed_file(filename):
    """
    Finds out if this file is allowed to be uploaded
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def nullable_email(email_str):
    if not email_str:
        return email_str
    else:
        return email(email_str)


def email(email_str):
    if validate_email(email_str):
        return email_str

    raise ValueError('{} is not a valid email'.format(email_str))


def hashed_password(password_str):
    if isinstance(password_str, basestring) and len(password_str) == 56:
        return password_str

    raise ValueError('Invalid password - expecting SHA224 - Received {} of length {} and type {}'.format(
        password_str, len(password_str), type(password_str)))


def secure_filename_input(orig_name):
    return secure_filename(orig_name)
 

class SubRequest:

    def __init__(self, orig_dict):
        self.json = orig_dict


class SubParser:

    __name__ = 'Nested parser'

    def __init__(self, child_parser):
        self.child_parser = child_parser
        self.child_parser.abort_on_error = False

    def __call__(self, item_to_parse):
        if isinstance(item_to_parse, list):
            return [self.child_parser.parse_args(req=SubRequest(item)) for item in item_to_parse]
        return self.child_parser.parse_args(req=SubRequest(item_to_parse))


class AllowedFileTypeMixin(object):
    "Mixin used of FileStorage subclasses to check the uploaded filetype"

    def __init__(self, *args, **kwargs):
        super(AllowedFileTypeMixin, self).__init__(*args, **kwargs)
        if not allowed_file(self.filename):
            raise ValueError('File type of {} is not accepted!'.format(self.filename))


class SafeFilenameStorage(FileStorage):

    def __init__(self, *args, **kwargs):
        super(SafeFilenameStorage, self).__init__(*args, **kwargs)
        if self.filename == 'file' and hasattr(self.stream, 'filename'):
            self.filename = self.stream.filename
        self.source_filename = self.filename
        self.filename = secure_filename(self.filename)


class AllowedFiletypeStorage(AllowedFileTypeMixin, FileStorage):
    pass


class AllowedSafeFilenameStorage(AllowedFileTypeMixin, SafeFilenameStorage):
    pass


class RequestParser(OrigReqParser):

    def __init__(self, *args, **kwargs):
        super(RequestParser, self).__init__(*args, **kwargs)
        self.abort_on_error = True

    def get_swagger_type(self, arg):
        try:
            if issubclass(arg.type, FileStorage):
                return 'file'
        except TypeError:
            ## this arg.type was not a class
            pass

        if callable(arg.type):
            return arg.type.__name__
        return arg.type

    def get_swagger_location(self, arg):

        if isinstance(arg.location, tuple):
            loc = arg.location[0]
        else:
            loc = arg.location.split(',')[0]

        if loc == "args":
            return "query"
        return loc


    def swagger_parameters(self):
        return [
            {
                'name': arg.name,
                'dataType': self.get_swagger_type(arg),
                'required': arg.required,
                'description': arg.help,
                'paramType': self.get_swagger_location(arg),
            }
            for arg in self.args
        ]

    def add_arguments(self, arguments_dict):
        for argument_name, kwargs in arguments_dict.iteritems():
            self.add_argument(argument_name, **kwargs)

    def parse_args(self, req=None, strict=False):
        from werkzeug.exceptions import HTTPException

        try:
            return super(RequestParser, self).parse_args(req, strict)
        except HTTPException as e:
            if self.abort_on_error:
                raise e
            else:
                raise ValueError(e.data['message'])


TEMPLATEDIR = "/tmp" # CK: hotfix to prevent ownership issues


def fullpath(filename, datadir=None):
    """
    "Normalizes" filename:  if it is full path, leaves it alone. Otherwise, prepends it with datadir.
    """

    if datadir == None:
        datadir = current_app.config['UPLOAD_FOLDER']

    result = filename

    # get user dir path
    datadir = upload_dir_user(datadir)

    if not(os.path.exists(datadir)):
        os.makedirs(datadir)
    if os.path.dirname(filename)=='' and not os.path.exists(filename):
        result = os.path.join(datadir, filename)

    return result


def templatepath(filename):
    return fullpath(filename, TEMPLATEDIR)


def upload_dir_user(dirpath, user_id = None):

    try:
        from flask.ext.login import current_user # pylint: disable=E0611,F0401

        # get current user
        if current_user.is_anonymous() == False:

            current_user_id = user_id if user_id else current_user.id

            # user_path
            user_path = os.path.join(dirpath, str(current_user_id))

            # if dir does not exist
            if not(os.path.exists(dirpath)):
                os.makedirs(dirpath)

            # if dir with user id does not exist
            if not(os.path.exists(user_path)):
                os.makedirs(user_path)

            return user_path
    except:
        return dirpath

    return dirpath


def normalize_obj(obj):
    """
    This is the main conversion function for Python data-structures into
    JSON-compatible data structures.

    Use this as much as possible to guard against data corruption!

    Args:
        obj: almost any kind of data structure that is a combination
            of list, numpy.ndarray, odicts etc

    Returns:
        A converted dict/list/value that should be JSON compatible
    """

    if isinstance(obj, list) or isinstance(obj, np.ndarray) or isinstance(obj, tuple):
        return [normalize_obj(p) for p in obj]

    if isinstance(obj, dict):
        return {str(k): normalize_obj(v) for k, v in obj.items()}

    if isinstance(obj, op.utils.odict):
        result = OrderedDict()
        for k, v in obj.items():
            result[str(k)] = normalize_obj(v)
        return result

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, float):
        if np.isnan(obj):
            return None

    if isinstance(obj, np.float64):
        if np.isnan(obj):
            return None
        else:
            return float(obj)

    if isinstance(obj, unicode):
        return str(obj)

    return obj


class OptimaJSONEncoder(flask.json.JSONEncoder):
    """
    Custom JSON encoder, supporting optima-specific objects.
    """
    def default(self, obj):
        # TODO preserve order of keys
        if isinstance(obj, op.parameters.Parameterset):
            return OrderedDict([(k, normalize_obj(v)) for (k, v) in obj.__dict__.iteritems()])

        if isinstance(obj, op.parameters.Par):
            return OrderedDict([(k, normalize_obj(v)) for (k, v) in obj.__dict__.iteritems()])

        if isinstance(obj, np.float64):
            return normalize_obj(obj)

        if isinstance(obj, np.ndarray):
            return [normalize_obj(p) for p in list(obj)]

        if isinstance(obj, np.bool_):
            return bool(obj)

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, op.utils.odict):  # never seems to get there
            return normalize_obj(obj)

        if isinstance(obj, op.project.Project):
            return None

        if isinstance(obj, op.results.Resultset):
            return None

        obj = normalize_obj(obj)

        return flask.json.JSONEncoder.default(self, obj)