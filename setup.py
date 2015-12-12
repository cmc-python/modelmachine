# -*- coding: utf-8 -*-

"""Model machine emulator.

Read the doc: <https://github.com/vslutov/modelmachine>
"""

from setuptools import setup, find_packages

VERSION = "0.0.7" # Don't forget fix in __main__.py

setup(name='modelmachine',
      version=VERSION,
      description=__doc__,
      maintainer='vslutov',
      maintainer_email='vslutov@yandex.ru',
      url='https://github.com/vslutov/modelmachine',
      license='WTFPL',
      platforms=['any'],
      classifiers=["Development Status :: 2 - Pre-Alpha",
                   "Environment :: Console",
                   "Intended Audience :: Education",
                   "Natural Language :: Russian",
                   "Natural Language :: English",
                   "Operating System :: Unix",
                   "Operating System :: Microsoft :: Windows",
                   "Programming Language :: Python :: 3 :: Only",
                   "Topic :: Education",
                   "Topic :: Utilities",
                   "Topic :: Scientific/Engineering"],
      install_requires=['pytest'],
      packages=find_packages(),
      include_package_data=True,
      entry_points={'console_scripts': ['modelmachine = modelmachine.__main__:exec_main']})
