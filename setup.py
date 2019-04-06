#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup

PACKAGE_NAME = 'roshammer'
VERSION = '0.0.1'


setup(
    name=PACKAGE_NAME,
    version=VERSION,
    python_requires='>=3.5',
    description='A general purpose fuzzer for the Robot Operating System',
    long_description=open('README.rst').read(),
    author='Chris Timperley',
    author_email='christimperley@googlemail.com',
    url='https://github.com/ChrisTimperley/roshammer',
    license='Apache License 2.0',
    install_requires=[
        'attrs~=19.1.0',
        'fluffycow>=0.0.5',
        'click~=7.0'
    ],
    packages=['roshammer'],
    keywords=['ros', 'fuzzing', 'docker'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ]
)
