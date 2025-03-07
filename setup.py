#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import runpy
import os

# Read version (adapted from Covasim)
cwd = os.path.abspath(os.path.dirname(__file__))
versionpath = os.path.join(cwd, 'optima', 'version.py')
version = runpy.run_path(versionpath)['version']

# Read README.md for description
with open(os.path.join(cwd,'README.md'), 'r') as f:
    long_description = f.read()

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GPLv3',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 2.7',
	'Programming Language :: Python :: 3.7',
]

setup(
    name='optima',
    version=version,
    author='Cliff Kerr, Robyn Stuart, David Kedziora, Amber Brown, Romesh Abeysuriya, George Chadderdon, Rowan Martin-Hughes, Anna Nachesa, David Wilson, and others',
    author_email='info@optimamodel.com',
    description='Software package for modeling HIV epidemics',
    long_description=long_description,
    url='http://github.com/optimamodel/optima',
    keywords=['optima'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'matplotlib>=1.4.2',
        'numpy>=1.10.1',
        'xlrd==1.2.0', #WARNING temporary to read xlsx files and needs to to be replaced with a migration to openpyxl
        'xlsxwriter==3.2.0', #3.2.2 breaks functionality (not investigated)
        'sciris>=3.0.0',
        'scipy',
    ],
)
