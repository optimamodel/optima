from flask_restful import fields


class Uuid(fields.String):
    pass


class Json(fields.Raw):
    pass


class LargeBinary(fields.Raw):
    pass


class LargeInt(fields.Integer):

    def format(self, value):
        try:
            if value is None:
                return self.default
            return int(float(value))
        except ValueError as ve:
            raise fields.MarshallingException(ve)
