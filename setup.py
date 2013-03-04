#!/usr/bin/env python
from distutils.core import setup, Extension

DISTUTILS_DEBUG=True

setup(name='pifacedigitalio',
	version='1.1',
	description='The PiFace Digital Input/Output module.',
	author='Thomas Preston',
	author_email='thomasmarkpreston@gmail.com',
	license='GPLv3+',
	url='http://pi.cs.man.ac.uk/interface.htm',
	py_modules=['pifacedigitalio'],
)
