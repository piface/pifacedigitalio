########
Examples
########

.. note:: Subtitute ``python3`` for ``python`` if you want to use Python 2.

Basic usage
===========

Set up::

    $ python3
    >>> import pifacedigitalio as p
    >>> p.init()       # initialises the PiFace Digital board
    >>> p.init(False)  # same as above without resetting ports

Playing with PiFace Digital::

    >>> pfd = p.PiFaceDigital() # creates a PiFace Digtal object

    >>> pfd.leds[1].turn_on()    # turn on the second LED
    >>> pfd.leds[2].toggle()     # toggle third LED
    >>> pfd.switches[3].value    # check the status of switch3
    0
    >>> pfd.relays[0].value = 1  # turn on the first relay

    >>> pfd.output_pins[6].value = 1
    >>> pfd.output_pins[6].turn_off()

    >>> pfd.input_pins[6].value
    0

    >>> pfd.output_port.all_off()
    >>> pfd.output_port.value = 0xAA
    >>> pfd.output_port.toggle()

    >>> bin(pfd.input_port.value)  # with the fourth switch pressed
    '0b1000'

You can talk to the components directly::

    >>> led0 = p.LED(0)  # create an LED object (pin0, board0)
    >>> led0.turn_on()   # turn on the LED
    >>> led0.value = 1   # turn on the LED

    >>> led3_2 = p.LED(3, 2)  # create an LED object (pin3, board2)
    >>> led3_2.turn_on()      # turn on the LED

    >>> switch2 = p.Switch(2) # create a Switch object (pin2, board0)
    >>> switch2.value         # is the switch pressed?
    0

Some functions you might want to use if objects aren't your thing (though, you
should probably be looking at `pifacecommon <https://github.com/piface/pifacecommon>`_ instead)::

    >>> p.digital_write(0, 1)    # writes pin0 (board0) high
    >>> p.digital_write(5, 1, 2) # writes pin5 on board2 high
    >>> p.digital_read(4)        # reads pin4 (on board0)
    0
    >>> p.digital_read(2, 3)     # reads pin2 (on board3)
    1


Polymorphism
============

    >>> class Chicken(pifacedigitalio.Relay):
    ...     def __init__(self):
    ...         super().__init__(0)
    ...     def wobble(self):
    ...         self.turn_on()
    ...
    >>> chick1 = Chicken()
    >>> chick1.wobble()      # Turns on relay0 (connected to a robot chicken)


Interrupts
==========

Instead of polling for input we can use the :class:`InputEventListener` to
register actions that we wish to be called on certain input events.

    >>> import pifacedigitalio
    >>> pifacedigitalio.init()
    >>> pfd = pifacedigitalio.PiFaceDigital()
    >>> def toggle_led0(event):
    ...     pfd.leds[0].toggle()
    ...
    >>> listener = pifacedigitalio.InputEventListener()
    >>> listener.register(0, pifacedigitalio.IODIR_ON, toggle_led0)
    >>> listener.activate()

When input 0 is pressed, led0 will be toggled. To stop the listener, call it's
``deactivate`` method:

    >>> listener.deactivate()

The :class:`Event` object has some interesting attributes. You can access them
like so::

    >>> import pifacedigitalio
    >>> pifacedigitalio.init()
    >>> def print_event_info(event):
    ...     print("Flag:     ", bin(event.interrupt_flag))
    ...     print("Capture:  ", bin(event.interrupt_capture))
    ...     print("Pin num:  ", event.pin_num)
    ...     print("Direction:", event.direction)
    ...
    >>> listener = pifacedigitalio.InputEventListener()
    >>> listener.register(0, pifacedigitalio.IODIR_OFF, print_event_info)
    >>> listener.activate()

This would print out the event informaion whenever you unpress switch 0::

    Flag:      0b00000001
    Capture:   0b11111110
    Pin num:   0
    Direction: 1
