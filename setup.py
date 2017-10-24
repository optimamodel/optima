#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages

with open("optima/version.py", "r") as f:
    version_file = {}
    exec(f.read(), version_file)
    version = version_file["version"]

try:
    from pypandoc import convert
except ImportError:
    import io
    def convert(filename, fmt):
        with io.open(filename, encoding='utf-8') as fd:
            return fd.read()

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GPLv3',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 2.7',
]

setup(
    name='optima',
    version=version,
    author='Cliff Kerr, Robyn Stuart, David Kedziora, Romesh Abeysuriya, Madhura Killedar, Anna Nachesa',
    author_email='info@optimamodel.com',
    description='Software package for modeling HIV epidemics',
    long_description=convert('README.md', 'md'),
    url='http://github.com/optimamodel/Optima',
    keywords=['optima'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'matplotlib>=1.4.2',
        'numpy>=1.10.1',
    ],
)
