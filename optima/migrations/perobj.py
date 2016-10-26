"""
Tools to make upgrading Python objects easier.
"""

def make_upgradeable(obj):
    """
    Make an arbritary Python class upgradable.
    """
    class Upgradeable(obj):

        def __setstate__(self, state):
            from optima.migrations.migrate import migrate_obj
            state = migrate_obj(self, state)
            self.__dict__.pop("_optimaversion")

        def __getstate__(self):
            state = self.__dict__

            from optima import __version__
            state["_optimaversion"] = __version__
            return state

    # Class decorating!
    Upgradeable.__name__ = obj.__name__
    Upgradeable.__module__ = obj.__module__

    return Upgradeable
