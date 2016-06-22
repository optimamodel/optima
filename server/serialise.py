import simplejson as json
from uuid import UUID

import optima
import numpy
import datetime
from dateutil import parser, tz


def default(o):

    if isinstance(o, (optima.Project, optima.settings.Settings)):
        o = {"optima_obj": o.__class__.__name__, "val": o.__dict__}

    if isinstance(o, optima.odict):
        o = {"optima_obj": "odict", "val": list(o.iteritems())}

    if isinstance(o, UUID):
        o = {"optima_obj": "UUID", "val": str(o.hex)}

    if isinstance(o, numpy.ndarray):
        o = {"optima_obj": "numpy.ndarray", "val": list(o)}

    if isinstance(o, datetime.datetime):
        o.replace(tzinfo=tz.tzlocal())
        o = {"optima_obj": "datetime.datetime", "val": o.isoformat(" ")}

    if isinstance(o, tuple):
        o = {"optima_obj": "tuple", "val": list(o)}

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


if __name__ == "__main__":

    p = optima.Project()
    js = json.dumps(p, default=default, tuple_as_array=False)
    z = json.loads(js, object_hook=decode)

    from deepdiff import DeepDiff
    from pprint import pprint

    print(js)

    print(DeepDiff(p.__dict__, z.__dict__))
