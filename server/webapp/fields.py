from flask_restful import fields


class Uuid(fields.String):
    pass


class Json(fields.Raw):
    pass


class LargeBinary(fields.Raw):
    pass
