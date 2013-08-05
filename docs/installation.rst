############
Installation
############

.. note:: Subtitute ``python3``/``easy_install3`` for
   ``python``/``easy_install`` if you want to install for Python 2.

Download the latest releases of
`pifacecommon <https://github.com/piface/pifacecommon/releases>`_ and
`pifacedigitalio <https://github.com/piface/pifacedigitalio/releases>`_.
Then install with::

    $ dpkg -i python3-pifacecommon_2.0.2-1_all.deb python3-pifacedigitalio_2.0.2-1_all.deb

Or you can install without using your package manager::

    $ git clone https://github.com/piface/pifacedigitalio.git
    $ cd pifacedigitalio
    $ sudo python3 setup.py install

You can also get pifacedigitalio from PyPi::

    $ sudo easy_install3 pifacedigitalio
