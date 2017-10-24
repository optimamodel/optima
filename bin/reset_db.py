import sys
import os

try:
    import server
except:
    sys.path.insert(0, os.path.abspath(".."))

import server.api
server.api.init_db()
