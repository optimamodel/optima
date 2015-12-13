from flask import Response
from flask import helpers
from flask.ext.login import login_required
from flask_restful import Resource


class ProjectDownload(Resource):

    @login_required
    def get(self, filename):
        """
        Download example Excel file.
        """
        example_excel_file_name = 'example.xlsx'
        static_folder = '../static'

        file_path = helpers.safe_join(static_folder, example_excel_file_name)
        options = {
            'cache_timeout': helpers.get_send_file_max_age(
                                            example_excel_file_name),
            'conditional': True,
            'attachment_filename': filename
        }
        return helpers.send_file(file_path, **options)
