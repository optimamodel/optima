# Ensure that the current folder is used, not the global defaults
import sys
import os
optimafolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, optimafolder) 

# Load Optima
from server import _autoreload
from server import _twisted_wsgi

# Run the server
_autoreload.main(_twisted_wsgi.run)
