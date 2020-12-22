############
Installation
############

Make sure you are using the lastest version of Raspbian::

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install ``pifacedigitalio`` with the following command:

    Python 3:
    $ sudo pip3 install pifacedigitalio

    Notice 1: Installation from Raspbian repository with apt is not longer the preferred way, take a look into `(pifacecommon issue #27) <https://github.com/piface/pifacecommon/issues/27#issuecomment-451400154/>`_
    
    Notice 2: Python 2 support is "end-of-life" since Jan 2020, refer to https://www.python.org/doc/sunset-python-2/

Test by running the ``blink.py`` program::

    $ python3 /usr/share/doc/python3-pifacedigitalio/examples/blink.py

Emulator
========
Install ``python3-pifacedigital-emulator`` with the following command::

    $ sudo apt-get install python3-pifacedigital-emulator

Start the emulator with::

    $ pifacedigital-emulator

.. note:: You must be in an X11 session (``startx``).
