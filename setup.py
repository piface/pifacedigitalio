import sys
import subprocess
from distutils.core import setup


PY3 = sys.version_info.major >= 3
PYTHON_CMD = "python3" if PY3 else "python"
PIFACECOMMON_MIN_VERSION = '2.0.0'
VERSION_FILE = "pifacedigitalio/version.py"


# change this to True if you just want to install the module by itself
MODULE_ONLY = False

INSTALL_PIFACECOMMON_CMD = \
    "git clone https://github.com/piface/pifacecommon.git && " \
    "cd pifacecommon && " \
    "{} setup.py install".format(PYTHON_CMD)


class InstallFailed(Exception):
    pass


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


def run_cmd(cmd, error_msg):
    success = subprocess.call([cmd], shell=True)
    if success != 0:
        raise InstallFailed(error_msg)


def install_pifacecommon():
    print("Installing the latest pifacecommon (with git).")
    run_cmd(INSTALL_PIFACECOMMON_CMD, "Failed to install pifacecommon.")


def check_pifacecommon():
    try:
        import pifacecommon.version
    except ImportError:
        print("pifacecommon is not installed.")
        install_pifacecommon()
    else:
        if pifacecommon.version.__version__ < PIFACECOMMON_MIN_VERSION:
            print("pifacecommon needs to be updated.")
            install_pifacecommon()


if "install" in sys.argv and not MODULE_ONLY:
    check_pifacecommon()


setup(
    name='pifacedigitalio',
    version=get_version(),
    description='The PiFace Digital I/O module.',
    author='Thomas Preston',
    author_email='thomasmarkpreston@gmail.com',
    url='http://piface.github.io/pifacecommon/index.html',
    packages=['pifacedigitalio'],
    long_description=open('README.md').read() + open('CHANGELOG').read(),
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or ",
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
