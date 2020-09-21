#!/usr/bin/env python3
from setuptools import setup

setup(
    name='kubecli',
    version='0.0.1',
    packages=['kubecli'],
    entry_points={
        'console_scripts': [
            'kubesh = kubecli.__main__:main'
        ]
    })
