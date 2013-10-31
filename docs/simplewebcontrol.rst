Simple Web Control
==================

You can control PiFace Digital from a web browser (or any network enabled
device) using the `simplewebcontrol.py` tool.

You can start the tool by running the following command on your Raspberry Pi::

    $ python3 /usr/share/doc/python3-pifacedigitalio/examples/simplewebcontrol.py

This will start a simple web server on port 8000 which you can access using
a web browser.

Type the following into the address bar of a browser on any machine in the
local network::

    http://192.168.1.3:8000

.. note:: Relace ``192.168.1.3`` with the IP address of your Raspberry Pi.

It will return a `JSON object <http://www.json.org/>`_ describing the current
state of PiFace Digital::

    {'input_port': 0, 'output_port': 0}


Controlling Output
------------------
You can set the output port using the URL::

    http://192.168.1.61:8000/?output_port=0xaa


Changing Port
-------------
You can specify which port you would like ``simplewebcontrol.py`` to use by
passing the port number as the first argument::

    $ python3 /usr/share/doc/python3-pifacedigitalio/examples/simplewebcontrol.py 12345
