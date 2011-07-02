# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='RevisionGraphPlugin',
    author='wadahiro',
    author_email='wadahiro@gmail.com',
    url = "http://sourceforge.jp/projects/shibuya-trac/wiki/plugins%2FRevisionGraphPlugin",
    description='Trac plugin for revision graph in a revision log page',
    version='0.1',
    license='New BSD',
    packages=find_packages(exclude=['*.tests*']),
    package_data={'reportinclude': ['htdocs/css/*.css', 'htdocs/js/*.js']},
    entry_points={
        'trac.plugins': [
            'revisiongraph = revisiongraph'
        ]
    },
)
