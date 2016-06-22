import simplejson as json
from uuid import UUID

import optima
import numpy
import datetime
import types
from dateutil import parser, tz


def default(o):

    if isinstance(o, (optima.Project, optima.settings.Settings)):
        o = {"optima_obj": o.__class__.__name__, "val": default(o.__dict__)}

    elif isinstance(o, optima.odict):
        o = {"optima_obj": "odict", "val": [(x, default(y)) for x, y in o.iteritems()]}

    elif isinstance(o, UUID):
        o = {"optima_obj": "UUID", "val": str(o.hex)}

    elif isinstance(o, numpy.ndarray):
        o = {"optima_obj": "numpy.ndarray", "val": list(o)}

    elif isinstance(o, datetime.datetime):
        o.replace(tzinfo=tz.tzlocal())
        o = {"optima_obj": "datetime.datetime", "val": o.isoformat(" ")}

    elif isinstance(o, tuple):
        o = {"optima_obj": "tuple", "val": [default(x) for x in o]}

    elif isinstance(o, (str, unicode, float, int, long, types.NoneType)):
        pass

    elif isinstance(o, list):
        o = [default(x) for x in o]

    elif isinstance(o, dict):
        o = {x:default(y) for x,y in o.iteritems()}

    else:
        raise ValueError("Don't know this.")

    return o

def decode(o):

    if isinstance(o, dict):

        if "optima_obj" in o:

            optima_obj = o["optima_obj"]
            val = o["val"]

            if optima_obj == "Project":

                o = object.__new__(optima.Project)
                o.__dict__ = val
                return o

            elif optima_obj == "Settings":

                o = object.__new__(optima.Settings)
                o.__dict__ = val
                return o

            elif optima_obj == "datetime.datetime":

                o = parser.parse(val)
                return o

            elif optima_obj == "UUID":
                o = UUID(val)
                return o

            elif optima_obj == "numpy.ndarray":
                o = numpy.array(val)
                return o

            elif optima_obj == "odict":

                o = optima.odict()
                for i in val:
                    o[i[0]] = i[1]

            elif optima_obj == "tuple":
                o = tuple(val)


            else:
                assert False, o

        return o

def dump(obj):

    return default(obj)



if __name__ == "__main__":

    p = optima.Project()

    print(json.dumps(dump(p)))

    js = json.dumps(dump(p))
    z = json.loads(js, object_hook=decode)

    from deepdiff import DeepDiff

    print(DeepDiff(p.__dict__, z.__dict__))
