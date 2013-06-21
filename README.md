pifacedigitalio
===============
The PiFace Digital Input/Output module ([PyPI](https://pypi.python.org/pypi/pifacedigitalio/)).

pifacedigitalio uses **Python 3** and is incompatible with 
Python 2. *You have to start Python 3 using `python3` and not `python`.*


Installation
============

    $ git clone https://github.com/piface/pifacedigitalio.git
    $ cd pifacedigitalio
    $ sudo ./install.sh

You may need to reboot for interrupts to work.


Building and Viewing Documentation
==================================

If you have [Sphinx](http://sphinx-doc.org/) installed:

    $ cd docs/
    $ make html
    $ cd _build/html/
    $ python3 -m http.server

Open a browser and go to http://localhost:8000.

Otherwise, just take a peek in the docs/ directory (mainly pifacedigital and
examples).