# Ensure that the current folder is used, not the global defaults
import sys
import os
sys.path.insert(0, os.path.abspath("..")) 

# Load Optima
from server import _autoreload
from server import _twisted_wsgi

# Run the server
_autoreload.main(_twisted_wsgi.run)
