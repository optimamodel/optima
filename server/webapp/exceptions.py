from werkzeug.exceptions import HTTPException

class BaseRESTException(HTTPException):
    code = 500
    _message = 'An unexpected error happened'

    def __init__(self):
        self.description = self._message
        super(HTTPException, self).__init__()

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
        super(BaseRESTException, self).__init__()
        if email is not None:
            self.description = 'User with e-mail "{}" already exists'.format(email)


class RecordDoesNotExist(BaseRESTException):

    code = 410
    _message = 'The resource you are looking for does not exist'
    _model = 'Resource'
    
    def __init__(self, id=None, model=None):
        super(BaseRESTException, self).__init__()
        if id is not None or model != 'Resource':
            elements = [
                'The {}'.format(model if model is not None else self._model),
                'with id "{}"'.format(id) if id is not None else 'you are looking for',
                'does not exist'
            ]
            self.description = ' '.join(elements)


class InvalidCredentials(BaseRESTException):
    code = 401
    description = 'The user or password provided are incorrect'


class ParamsMissing(BaseRESTException):
    code = 400
    _message = 'Missing required parameters'

    def __init__(self, param):
        super(BaseRESTException, self).__init__()
        self.description = "Missing '%s' required parameter" % (param)


class NotFound(BaseRESTException):
    code = 404
    _message = 'The item you are looking for does not exist'
    _model = 'Resource'

    def __init__(self, id=None, model=None):
        super(BaseRESTException, self).__init__()
        if id is not None or model != 'Resource':
            elements = [
                'The {}'.format(model if model is not None else self._model),
                'with id "{}"'.format(id) if id is not None else 'you are looking for',
                'does not exist'
            ]
            self.description = ' '.join(elements)

class ProjectNotFound(NotFound):

    _model = 'project'
