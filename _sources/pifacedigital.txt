##############
PiFace Digital
##############
PiFace Digital has eight inputs, eight outputs, eight LED's, two relays and
four switches.

Outputs
=======
The eight output pins are located at the top of the board (near the LEDs). The
outputs are open collectors, they can be thought of as switches connecting to
ground. This offers greater flexibility so that PiFace Digital can control devices
that operate using different voltages. The ninth pin provides 5V for connecting
circuits to.

LEDs
----
The LED's are connected in parallel to each of the outputs. This means that
when you set output pin 4 high, LED 4 illuminates.

    >>> import pifacedigitalio
    >>> pifacedigital = pifacedigitalio.PiFaceDigital()
    >>> pifacedigital.output_pins[4].turn_on()  # this command does the same thing...
    >>> pifacedigital.leds[4].turn_on()  # ...as this command

Relays
------
The two Relays are connected in parallel to output pins 0 and 1 respectively.
When you set output pin 0 high, LED 0 illuminates and Relay 0 activates.

    >>> import pifacedigitalio
    >>> pifacedigital = pifacedigitalio.PiFaceDigital()
    >>> pifacedigital.output_pins[0].turn_on()  # this command does the same thing...
    >>> pifacedigital.leds[0].turn_on()  # ...as this command...
    >>> pifacedigital.relays[0].turn_on()  # ...and this command...

When activated, the relay bridges the top and middle pins. When deactivated the
bottom two are connected.

Relay activated::

    [Top Pin   ]
    [Common    ]
     Bottom Pin

Relay Deactivated::

     Top Pin
    [Common    ]
    [Bottom Pin]

Inputs
======
The eight input pins detect a connection to ground (provided as the ninth pin).
The four switches are connected in parallel to the first four input pins. The
inputs are *pulled up* to 5V. This can be turned off so that the inputs float.

    >>> import pifacedigitalio
    >>> pifacedigital = pifacedigitalio.PiFaceDigital()
    >>>
    >>> # without anything pressed
    >>> pifacedigital.input_port.value
    0
    >>> pifacedigital.input_pins[0].value
    0
    >>> pifacedigital.switches[0].value
    0
    >>>
    >>> # pressing the third switch
    >>> pifacedigital.input_port.value
    8
    >>> bin(pifacedigital.input_port.value)
    0b100
    >>> pifacedigital.input_pins[2].value  # this command is the same as...
    1
    >>> pifacedigital.switches[2].value  # ...this command
    1
