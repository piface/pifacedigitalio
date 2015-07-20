########
Examples
########

Basic usage
===========

::

    >>> import pifacedigitalio

    >>> pfd = pifacedigitalio.PiFaceDigital() # creates a PiFace Digtal object

    >>> pfd.leds[1].turn_on()    # turn on/set high the second LED
    >>> pfd.leds[1].set_high()   # turn on/set high the second LED
    >>> pfd.leds[2].toggle()     # toggle third LED
    >>> pfd.switches[3].value    # check the logical status of switch3
    0
    >>> pfd.relays[0].value = 1  # turn on/set high the first relay

    >>> pfd.output_pins[6].value = 1
    >>> pfd.output_pins[6].turn_off()

    >>> pfd.input_pins[6].value
    0

    >>> pfd.output_port.all_off()
    >>> pfd.output_port.value = 0xAA
    >>> pfd.output_port.toggle()

    >>> bin(pfd.input_port.value)  # fourth switch pressed (logical input port)
    '0b1000'

    >>> bin(pfd.gpiob.value)  # fourth switch pressed (physical input port)
    '0b11110111'

    >>> pfd.deinit_board()  # disables interrupts and closes the file

.. note: Inputs are active low on GPIO Port B. This is hidden in software
   unless you inspect the GPIOB register.

Here are some functions you might want to use if objects aren't your thing::

    >>> import pifacedigitalio as p
    >>> p.init()
    >>> p.digital_write(0, 1)    # writes pin0 high
    >>> p.digital_write(5, 1, 2) # writes pin5 on board2 high
    >>> p.digital_read(4)        # reads pin4 (on board0)
    0
    >>> p.digital_read(2, 3)     # reads pin2 (on board3)
    1
    >>> p.deinit()

.. note: These are just wrappers around the PiFaceDigital object.

Interrupts
==========

Instead of polling for input we can use the :class:`InputEventListener` to
register actions that we wish to be called on certain input events.

    >>> import pifacedigitalio
    >>> def toggle_led0(event):
    ...     event.chip.leds[0].toggle()
    ...
    >>> pifacedigital = pifacedigitalio.PiFaceDigital()
    >>> listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
    >>> listener.register(0, pifacedigitalio.IODIR_FALLING_EDGE, toggle_led0)
    >>> listener.activate()

When input 0 is pressed, led0 will be toggled. To stop the listener, call it's
``deactivate`` method:

    >>> listener.deactivate()

The :class:`Event` object has some interesting attributes. You can access them
like so::

    >>> import pifacedigitalio
    >>> pifacedigital = pifacedigitalio.PiFaceDigital()
    >>> listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
    >>> listener.register(0, pifacedigitalio.IODIR_RISING_EDGE, print)
    >>> listener.activate()

This would print out the event information whenever you un-press switch 0::

    interrupt_flag:    0b1
    interrupt_capture: 0b11111111
    pin_num:           0
    direction:         1
    chip:              <pifacedigitalio.core.PiFaceDigital object at 0xb682dab0>
    timestamp:         1380893579.447889


Exit from interrupt
-------------------
In some cases you may want to deactivate the listener and exit your program
on an interrupt (press switch to exit, for example). Since each method
registered to an interrupt is run in a new thread and you can only
deactivate a listener from within the same thread that activated it, you
cannot deactivate a listener from a method registered to an interrupt. That is,
you cannot do the following because the ``deactivate_listener_and_exit()``
method is started in a different thread::

    import sys
    import pifacedigitalio


    listener = None


    def deactivate_listener_and_exit(event):
        global listener
        listener.deactivate()
        sys.exit()


    pifacedigital = pifacedigitalio.PiFaceDigital()
    listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
    listener.register(0,
                      pifacedigitalio.IODIR_FALLING_EDGE,
                      deactivate_listener_and_exit)
    listener.activate()

One solution is to use a `Barrier <https://docs.python.org/3/library/threading.html#barrier-objects>`_ synchronisation object. Each thread calls ``wait()`` on the barrier and
then blocks. After the final thread calls ``wait()`` all threads are unblocked.
Here is an example program which successfully exits on an interrupt::


    import sys
    import threading
    import pifacedigitalio


    exit_barrier = threading.Barrier(2)


    def deactivate_listener_and_exit(event):
        global exit_barrier
        exit_barrier.wait()


    pifacedigital = pifacedigitalio.PiFaceDigital()
    listener = pifacedigitalio.InputEventListener(chip=pifacedigital)
    listener.register(0,
                      pifacedigitalio.IODIR_FALLING_EDGE,
                      deactivate_listener_and_exit)
    listener.activate()
    exit_barrier.wait() # program will wait here until exit_barrier releases
    listener.deactivate()
    sys.exit()
