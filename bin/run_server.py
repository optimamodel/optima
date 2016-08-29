import sys
import os

try:
    import server
except:
    sys.path.insert(0, os.path.abspath("server/src/"))

import _autoreload
import _twisted_wsgi

_autoreload.main(_twisted_wsgi.run)
