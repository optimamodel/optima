import simplejson as json
from uuid import UUID

import optima
import numpy
import datetime
import types
from dateutil import parser, tz

import uuid


def dump(obj):

    obj_registry = {}

    def default(r):

        if isinstance(r, optima.odict):
            o = {"optima_obj": "odict", "val": [(x, default(y)) for x, y in r.iteritems()]}

        elif isinstance(r, UUID):
            o = {"optima_obj": "UUID", "val": str(r.hex)}

        elif isinstance(r, numpy.ndarray):
            o = {"optima_obj": "numpy.ndarray", "val": [default(x) for x in r]}

        elif isinstance(r, numpy.bool_):
            o = {"optima_obj": "numpy.bool_", "val": bool(r)}

        elif r == numpy.nan:
            o = {"optima_obj": "numpy.NaN"}

        elif isinstance(r, datetime.datetime):
            r.replace(tzinfo=tz.tzlocal())
            o = {"optima_obj": "datetime.datetime", "val": r.isoformat(" ")}

        elif isinstance(r, tuple):
            o = {"optima_obj": "tuple", "val": [default(x) for x in r]}

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

                my_id = uuid.uuid4().hex

                obj_registry[r] = [my_id, None]

                try:
                    results = default(r.__getstate__())
                except AttributeError:
                    results = default(r.__dict__)

                q = {
                    "optima_obj": r.__class__.__name__,
                    "val": results,
                    "id": my_id
                }
                obj_registry[r][1] = q

            o = {
                "optima_obj": "reference",
                "ref": obj_registry[r][0]
            }

        return o

    schema = default(obj)
    new_registry = {x[0]:x[1] for x in obj_registry.values()}

    return json.dumps({
        "registry": new_registry,
        "schema": schema}, ensure_ascii=False)


decode_structs = {
    "Project": optima.Project,
    "Settings": optima.Settings,
    "Parscen": optima.Parscen,
    "Budgetscen": optima.Budgetscen,
    "Programset": optima.Programset,
    "Covout": optima.programs.Covout
}


def loads(a):

    registry = a["registry"]
    schema = a["schema"]

    def decode(o):

        if isinstance(o, dict):

            if "optima_obj" in o:

                optima_obj = o["optima_obj"]

                val = o.get("val")

                if optima_obj == "reference":
                    print(o)
                    item = registry[o["ref"]]
                    print(item)
                    o = decode(item)

                elif optima_obj in decode_structs:

                    o = object.__new__(decode_structs[optima_obj])

                    state = {x:decode(y) for x,y in val.items()}
                    try:
                        o.__setstate__(state)
                    except AttributeError:
                        o.__dict__ = state

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
                        print(i)
                        print(i[0])
                        print(i[1])
                        o[i[0]] = decode(i[1])

                elif optima_obj == "tuple":
                    o = tuple(val)


                else:
                    assert False, o

            return o

        return o

    return decode(schema)



if __name__ == "__main__":

    p = optima.Project()

    with open("/tmp/test.json", "rb") as f:
      z = json.loads(f.read())
      k = loads(z)
      print(k)


    from deepdiff import DeepDiff

    print(DeepDiff(p.__dict__, z.__dict__))
