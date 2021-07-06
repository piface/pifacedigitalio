pifacedigitalio
===============
The PiFace Digital Input/Output module ([PyPI](https://pypi.python.org/pypi/pifacedigitalio/)).

Use this module to use PiFace Digital and PiFace Digital 2 hardware in Python3

Install
=======

Make sure you are using the lastest version of Raspbian:

    $ sudo apt-get update
    $ sudo apt-get upgrade

Enable SPI (e.g. use raspi-config)

    $ sudo raspi-config
    
    select `Interface Options` > `SPI` > `Yes` and then select `Finish`

If you need to install pip3

    $ sudo apt install python3-pip

Install `pifacedigitalio` with the following command:

    Python 3:
    $ sudo pip3 install pifacecommon
    $ sudo pip3 install pifacedigitalio

 * Notice 1: Installation from Raspbian repository with apt is not longer the preferred way, take a look into [https://github.com/piface/pifacecommon/issues/27#issuecomment-451400154](issue 27)    
 * Notice 2: Python 2 support is "end-of-life" since Jan 2020, refer to https://www.python.org/doc/sunset-python-2/

Examples
========

To run an example program clone this repo

    $ git clone https://github.com/piface/pifacedigitalio.git

Test by running the `blink.py` program:

    $ python3 pifacedigitalio/examples/blink.py

Documentation
=============

[http://pifacedigitalio.readthedocs.org/](http://pifacedigitalio.readthedocs.org/)
