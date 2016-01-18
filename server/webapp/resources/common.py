from flask_restful import fields
from server.webapp.utils import RequestParser
from server.webapp.inputs import AllowedSafeFilenameStorage


file_resource = {
    'file': fields.String,
    'result': fields.String,
}
file_upload_form_parser = RequestParser()
file_upload_form_parser.add_argument('file', type=AllowedSafeFilenameStorage, location='files', required=True)
