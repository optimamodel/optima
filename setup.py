#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages
from optima import __version__
try:
    from pypandoc import convert
except ImportError:
    import io

    def convert(filename, fmt):
        with io.open(filename, encoding='utf-8') as fd:
            return fd.read()

DESCRIPTION = 'Optima BE'

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: Other/Proprietary License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 2.7',
]

setup(
    name='optima',
    version=__version__,
    author='Cliff Kerr, Robyn Stuart, David Kedziora, Anna Nachesa',
    author_email='info@optima.com',
    description=DESCRIPTION,
    long_description=convert('README.md', 'rst'),
    url='https://github.com/optima/optima',
    keywords=['optima'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=['optima']),
    include_package_data=True,
    install_requires=[
        'matplotlib==1.4.2',
        'numpy==1.10.1',
        'pytz==2014.7',
        'python-dateutil==2.2',
        'mpld3==0.2',
    ],
)

