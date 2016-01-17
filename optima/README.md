Optima
======

Installation
-----

To install, run `python setup.py develop` in the root repository directory. This will add Optima to the system path. Optima can then be used via Python. Note: do **not** use `python setup.py install`, as this will copy the source code into your system Python directory, and you won't be able to modify or update it easily. To uninstall, run `python setup.py develop --uninstall`.

Note that to use the frontend, you'll also need to follow the installation instructions listed in the README files in the root directory, as well as in the `client` and `server` folders.

Usage
-----

See the scripts in the `tests` folder for usage examples. In particular, `testworkflow.py` shows a typical usage example.
