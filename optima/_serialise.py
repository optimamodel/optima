import simplejson as json

import optima
import numpy
import datetime
import types
import uuid
import zlib

from dateutil import parser, tz


def dumps(obj):

    obj_registry = {}
    id_number = [0]

    def default(r):

        if isinstance(r, optima.odict):
            o = {
                "obj": "odict",
                "val": [(default(x), default(y)) for x, y in r.iteritems()]}

        elif isinstance(r, uuid.UUID):
            o = {"obj": "UUID", "val": str(r.hex)}

        elif isinstance(r, numpy.ndarray):
            o = {"obj": "numpy.ndarray", "val": [default(x) for x in r]}

        elif isinstance(r, numpy.bool_):
            o = bool(r)

        elif r == numpy.nan:
            o = {"obj": "numpy.NaN"}

        elif isinstance(r, datetime.datetime):
            r.replace(tzinfo=tz.tzlocal())
            o = {"obj": "datetime", "val": r.isoformat(" ")}

        elif isinstance(r, tuple):
            o = {"obj": "tuple", "val": [default(x) for x in r]}

        elif isinstance(r, (str, unicode, float, int, long, types.NoneType, bool)):
            o = r
            pass

        elif isinstance(r, list):
            o = [default(x) for x in r]

        elif isinstance(r, dict):
            o = {}
            for x,y in r.items():
                o[x] = default(y)

        else:
            if not r in obj_registry:

                my_id = id_number[0]
                id_number[0] += 1

                obj_registry[r] = [my_id, None]

                try:
                    results = default(r.__getstate__())
                except AttributeError:
                    results = default(r.__dict__)

                q = {
                    "obj": r.__class__.__name__,
                    "val": results,
                    "id": my_id
                }
                obj_registry[r][1] = q

            o = {
                "obj": "ref",
                "ref": obj_registry[r][0]
            }

        return o

    schema = default(obj)
    new_registry = {x[0]:x[1] for x in obj_registry.values()}

    dumped = json.dumps({
        "registry": new_registry,
        "schema": schema}, ensure_ascii=False, separators=(',',':'))

    return zlib.compress(dumped, 6)


decode_structs = {
    "Project": optima.Project,
    "Settings": optima.Settings,
    "Parscen": optima.Parscen,
    "Budgetscen": optima.Budgetscen,
    "Programset": optima.Programset,
    "Covout": optima.programs.Covout,
    "Resultset": optima.Resultset,
    "Parameterset": optima.Parameterset,
    "Constant": optima.Constant,
    "Popsizepar": optima.Popsizepar,
    "Timepar": optima.Timepar,
    "Result": optima.Result,
    "Program": optima.Program,
    "Costcov": optima.programs.Costcov
}


def loads(input):

    a = json.loads(zlib.decompress(input))

    registry = a["registry"]
    schema = a["schema"]
    loaded = {}

    def decode(o):

        if isinstance(o, list):
            return [decode(x) for x in o]

        elif isinstance(o, dict):

            if "obj" in o:

                obj = o["obj"]
                val = o.get("val")

                if obj == "ref":

                    ref = o["ref"]
                    return decode(registry[str(ref)])

                elif obj in decode_structs:

                    if o["id"] in loaded:
                        return loaded[o["id"]]

                    new = object.__new__(decode_structs[obj])

                    loaded[o["id"]] = new

                    state = {x:decode(y) for x,y in val.items()}
                    try:
                        new.__setstate__(state)
                    except AttributeError:
                        new.__dict__ = state

                    return new

                elif obj == "datetime":
                    o = parser.parse(val)
                    return o

                elif obj == "UUID":
                    o = uuid.UUID(val)
                    return o

                elif obj == "numpy.ndarray":
                    o = numpy.array([decode(x) for x in val])
                    return o

                elif obj == "odict":

                    o = optima.odict()

                    for i in val:
                        key = decode(i[0])
                        val = decode(i[1])

                        o[key] = val

                elif obj == "tuple":
                    o = tuple([decode(x) for x in val])

                else:
                    assert False, str(o)[0:1000]
            else:
                return {decode(x):decode(y) for x,y in o.iteritems()}

            return o

        return o

    done = decode(schema)
    return done
