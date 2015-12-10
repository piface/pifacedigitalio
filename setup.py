import sys
from distutils.core import setup


# PY3 = sys.version_info.major >= 3  # major is not available in python2.6
PY3 = sys.version_info[0] >= 3
PIFACECOMMON_MIN_VERSION = '3.0.0'
VERSION_FILE = "pifacedigitalio/version.py"


def get_version():
    if PY3:
        version_vars = {}
        with open(VERSION_FILE) as f:
            code = compile(f.read(), VERSION_FILE, 'exec')
            exec(code, None, version_vars)
        return version_vars['__version__']
    else:
        execfile(VERSION_FILE)
        return __version__


setup(
    name='pifacedigitalio',
    version=get_version(),
    description='The PiFace Digital I/O module.',
    author='Thomas Preston',
    author_email='thomas.preston@openlx.org.uk',
    url='http://piface.github.io/pifacedigitalio/',
    packages=['pifacedigitalio'],
    long_description=open('README.md').read() + open('CHANGELOG').read(),
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or "
        "later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='piface digital raspberrypi openlx',
    license='GPLv3+',
    requires=['pifacecommon (>='+PIFACECOMMON_MIN_VERSION+')']
)
