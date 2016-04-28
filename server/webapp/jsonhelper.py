import json
import flask.json
import optima as op
import numpy as np
from collections import OrderedDict


def normalize_obj(obj):
    """
    This is the main conversion function for Python data-structures into
    JSON-compatible data structures.

    Use this as much as possible to guard against data corruption!

    Args:
        obj: almost any kind of data structure that is a combination
            of list, numpy.ndarray, odicts etc

    Returns:
        A converted dict/list/value that should be JSON compatible
    """

    if isinstance(obj, list) or isinstance(obj, np.ndarray) or isinstance(obj, tuple):
        return [normalize_obj(p) for p in obj]

    if isinstance(obj, dict):
        return {str(k): normalize_obj(v) for k, v in obj.items()}

    if isinstance(obj, op.utils.odict):
        result = OrderedDict()
        for k, v in obj.items():
            result[str(k)] = normalize_obj(v)
        return result

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, float):
        if np.isnan(obj):
            return None

    if isinstance(obj, np.float64):
        if np.isnan(obj):
            return None
        else:
            return float(obj)

    return obj



class OptimaJSONEncoder(flask.json.JSONEncoder):

    """
    Custom JSON encoder, supporting optima-specific objects.
    """

    def default(self, obj):
        """
        Support additional data types when encoding to JSON.
        """
        if isinstance(obj, op.parameters.Parameterset):  # TODO preserve order of keys
            return OrderedDict([(k, normalize_obj(v)) for (k, v) in obj.__dict__.iteritems()])

        if isinstance(obj, op.parameters.Par):
            return OrderedDict([(k, normalize_obj(v)) for (k, v) in obj.__dict__.iteritems()])

        if isinstance(obj, np.float64):
            return normalize_obj(obj)

        if isinstance(obj, np.ndarray):
            return [normalize_obj(p) for p in list(obj)]

        if isinstance(obj, np.bool_):
            return bool(obj)

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, op.utils.odict):  # never seems to get there
            return normalize_obj(obj)

        if isinstance(obj, op.project.Project):
            return None

        if isinstance(obj, op.results.Resultset):
            return None

        obj = normalize_obj(obj)

        return flask.json.JSONEncoder.default(self, obj)
