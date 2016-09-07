#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
import litterbox


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'future >= 0.15.0',
    'RPi.GPIO',
    'tqdm',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='litterbox',
    version=litterbox.__version__,
    description="A set of tools to manage all the crap for the CAT Board.",
    long_description=readme + '\n\n' + history,
    author=litterbox.__author__,
    author_email=litterbox.__email__,
    url='https://github.com/xesscorp/litterbox',
#    packages=['litterbox',],
    packages=setuptools.find_packages(),
    entry_points={'console_scripts':['litterbox = litterbox.__main__:main']},
    package_dir={'litterbox':
                 'litterbox'},
    include_package_data=True,
    package_data={'litterbox': ['*.gif', '*.png']},
    scripts=[],
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='litterbox',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
