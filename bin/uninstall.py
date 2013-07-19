import os
import sys
import shutil
import subprocess


PY3 = sys.version_info.major >= 3


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


DIST_PACKAGES = "/usr/local/lib/python{major}.{minor}/dist-packages/".format(
    major=sys.version_info.major, minor=sys.version_info.minor)
PIFACE_DIGITAL_PACKAGE_DIR = DIST_PACKAGES + "pifacedigitalio/"
VERSION_FILE = 'pifacedigitalio/version.py'
PIFACE_DIGITALMON_EGG_INFO = \
    DIST_PACKAGES + "pifacedigitalio-{version}.egg-info".format(
        version=get_version())


def remove_files():
    print("Removing files.")
    shutil.rmtree(PIFACE_DIGITAL_PACKAGE_DIR)
    os.remove(PIFACE_DIGITALMON_EGG_INFO)


if __name__ == '__main__':
    remove_files()
