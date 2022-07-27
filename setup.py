#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# Read version (adapted from Atomica)
cwd = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(cwd, 'optima', 'version.py'), 'r') as f:
    version = [x.split('=')[1].replace('"','').strip() for x in f if x.startswith('version =')][0]

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
        'xlrd',
        'xlsxwriter',
        'sciris',
    ],
)
