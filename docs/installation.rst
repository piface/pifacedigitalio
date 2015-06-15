############
Installation
############

Make sure you are using the lastest version of Raspbian::

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install ``pifacedigitalio`` (for Python 3 and 2) with the following command::

    $ sudo apt-get install python{,3}-pifacedigitalio

Test by running the ``blink.py`` program::

    $ python3 /usr/share/doc/python3-pifacedigitalio/examples/blink.py

Emulator
========
Install ``python3-pifacedigital-emulator`` with the following command::

    $ sudo apt-get install python3-pifacedigital-emulator

Start the emulator with::

    $ pifacedigital-emulator

.. note:: You must be in an X11 session (``startx``).
