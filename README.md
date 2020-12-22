pifacedigitalio
===============
The PiFace Digital Input/Output module ([PyPI](https://pypi.python.org/pypi/pifacedigitalio/)).


Documentation
=============

[http://pifacedigitalio.readthedocs.org/](http://pifacedigitalio.readthedocs.org/)

You can also find the documentation and some examples installed at:

    /usr/share/doc/python3-pifacedigitalio/

Install
=======

Make sure you are using the lastest version of Raspbian:

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install `pifacedigitalio` with the following commands:

    Python 3:
    $ sudo pip3 install pifacedigitalio

    Notice 1: Installation from Raspbian repository with apt is not longer the preferred way, take a look into [https://github.com/piface/pifacecommon/issues/27#issuecomment-451400154](issue 27)
    
    Notice 2: Python 2 support is "end-of-life" since Jan 2020, refer to https://www.python.org/doc/sunset-python-2/

Test by running the `blink.py` program:

    $ python3 /usr/share/doc/python3-pifacedigitalio/examples/blink.py
