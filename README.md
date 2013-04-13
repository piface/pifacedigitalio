pifacedigitalio
===============

The PiFace Digital Input/Output module.

*The PiFace Digital IO module uses Python 3 and is incompatible with Python 2*

Installation
============
### Enabling the SPI module
PiFace Digital communicates with the Raspberry Pi using the SPI interface.
The SPI interface driver is included in the later Raspbian distributions
but is not enabled by default.

To load the SPI driver manually, type:

    # modprobe spi-bcm2708

*This will not persist after a reboot.* To permanently enable the SPI module
comment out the spi module blacklist line in /etc/modprobe.d/raspi-blacklist.conf
(you will have to be root).

### Installing the software
    $ sudo ./install.sh

If gpio-admin was installed then make sure to log out and then back in again.

Examples
=======
Basic usage
-----------

    >>> import pifacedigitalio as p
    >>> p.init()       # initialises the PiFace Digital board 
    >>> p.init(False)  # same as above w/out resetting ports
    
    >>> pfd = p.PiFaceDigital(1) # creates a PiFace Digtal object (board1)
    >>> pfd.leds[1].turn_on()    # turn on the second LED
    >>> pfd.leds[2].toggle()     # toggle third LED
    >>> pfd.switches[3].value    # check the status of switch3
    0
    >>> pfd.relays[0].value = 1  # turn on the first relay

    >>> led0 = p.LED(0)  # create an LED object (pin0, board0)
    >>> led0.turn_on()   # turn on the LED
    >>> led0.value = 1   # turn on the LED

    >>> led3_2 = p.LED(3, 2)  # create an LED object (pin3, board2)
    >>> led3_2.turn_on()      # turn on the LED

    >>> switch2 = p.Switch(2) # create a Switch object (pin2, board0)
    >>> switch2.value         # is the switch pressed?
    0
    >>>

    >>> p.digital_write(0, 1)    # writes pin0 (board0) high
    >>> p.digital_write(5, 1, 2) # writes pin5 on board2 high
    >>> p.digital_read(4)        # reads pin4 (on board0)
    0
    >>> p.digital_read(2, 3)     # reads pin2 (on board3)
    1

Polymorphism
------------
    >>> class Chicken(pfio.Relay):
    ...     def __init__(self):
    ...         pfio.Relay.__init__(self, 0)
    ...     def wobble(self):
    ...         self.turn_on()
    ...
    >>> chick1 = Chicken()
    >>> chick1.wobble()      # Turns on relay0 (connected to a robot chicken)

Interupts
---------
    >>> import pifacedigitalio as p
    >>> p.init()
    >>> pfd = p.PiFaceDigital()
    >>>
    >>> # create two functions
    >>> def test(interupt_bit, input_byte):
    ...     print("Input pins: %s" % bin(input_byte))
    ...     pfd.leds[0].toggle()
    ...
    >>> def test2(interupt_bit, input_byte):
    ...     print("Input pins: %s" % bin(input_byte))
    ...     pfd.leds[7].toggle()
    ...
    >>> ifm = p.InputFunctionMap()       # create the input function map
    >>> ifm.register(0, 0, test)         # and register some input/callbacks
    >>> ifm.register(index=3, into=0, callback=test2, board=0)
    >>> p.wait_for_input(ifm, loop=True) # loop=False, wait_for_input() will return
