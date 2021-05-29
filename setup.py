#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='gk8-scrap',
    version='0.0.0',
    description='Find shortest path to coinbase',
    author='olegsivokon@gmail.com',
    url='https://github.com/wvxvw/gk8-assignment',
    license='MIT',
    packages=['gk_scrap'],
    scripts=[
        'bin/gk8-scrap',
    ],
)
