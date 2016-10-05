from werkzeug.exceptions import HTTPException


class BaseRESTException(HTTPException):
    code = 500
    _message = 'An unexpected error happened'

    def __init__(self):
        self.description = self._message
        super(BaseRESTException, self).__init__()

    def to_dict(self):
        return {
            'status_code': self.code,
            'userMessage': self.description,
            'internalMessage': self.__str__()
        }


class UserAlreadyExists(BaseRESTException):
    code = 409
    _message = 'User already exists'

    def __init__(self, email=None):
        super(UserAlreadyExists, self).__init__()
        if email is not None:
            self.description = 'User with e-mail "{}" already exists'.format(email)


class DuplicateProgram(BaseRESTException):
    code = 400
    _message = 'Duplicate program short name'

    def __init__(self, short=None):
        super(DuplicateProgram, self).__init__()
        if short is not None:
            self.description = 'Duplicate program short name: {}'.format(short)


class RecordDoesNotExist(BaseRESTException):
    code = 410
    _message = 'The resource you are looking for does not exist'
    _model = 'Resource'

    def __init__(self, id=None, model=None, project_id=None):
        super(RecordDoesNotExist, self).__init__()
        if id is not None or model != 'Resource':
            elements = [
                'The {}'.format(model if model is not None else self._model),
                'with id {}'.format(id) if id is not None else 'you are looking for',
                'in project {}'.format(project_id) if project_id else '',
                'does not exist'
            ]
            self.description = ' '.join(elements)


class ProjectDoesNotExist(RecordDoesNotExist):
    _model = 'project'


class ParsetDoesNotExist(RecordDoesNotExist):
    _model = 'parset'


class ParsetAlreadyExists(BaseRESTException):
    def __init__(self, project_id, name):
        super(ParsetAlreadyExists, self).__init__()
        self.code = 406
        self.description = 'Parset "{0}" already exists in project {1}'.format(name, project_id)


class ProgsetDoesNotExist(RecordDoesNotExist):
    _model = 'progset'

class ScenarioDoesNotExist(RecordDoesNotExist):
    _model = 'scenario'

class ProgramDoesNotExist(RecordDoesNotExist):
    _model = 'program'


class InvalidCredentials(BaseRESTException):
    code = 401
    description = 'The user or password provided are incorrect'


class InvalidFileType(BaseRESTException):
    code = 406
    _message = 'This file type is not accepted!'

    def __init__(self, filename=None):
        super(InvalidFileType, self).__init__()
        if filename is None:
            self.description = self._message
        else:
            self.description = 'File type of {} is not accepted!'.format(filename)


class UserDoesNotExist(RecordDoesNotExist):
    _model = 'user'