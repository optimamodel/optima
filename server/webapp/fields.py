from flask_restful import fields


class Uuid(fields.String):
    pass

class Json(fields.String):
    pass

class LargeBinary(fields.Raw):
    pass
