#!/bin/bash
python2 setup.py --command-packages=stdeb.command sdist_dsc

version=$(cat pifacedigitalio/version.py | sed 's/.*\([0-9]\.[0-9]\.[0-9]\).*/\1/')
cd deb_dist/pifacedigitalio-$version/

cp {../../dpkg-files,debian}/control
cp {../../dpkg-files,debian}/copyright
cp {../../dpkg-files,debian}/rules
cp {../../dpkg-files,debian}/python-pifacedigitalio.install
cp {../../dpkg-files,debian}/python3-pifacedigitalio.install

ls ../../examples/ | while read example
do
    echo ../../examples/$example >> debian/python-pifacedigitalio.examples
    echo ../../examples/$example >> debian/python3-pifacedigitalio.examples
done

dpkg-buildpackage #-us -uc
