pifacedigitalio
===============

The PiFace Digital Input/Output module.

*The PiFace Digital IO module uses Python 3 and is incompatible with Python 2*

Installation
============
    $ sudo ./install.sh

You may need to reboot for interrupts to work.

Examples
=======
### Basic usage

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

### Polymorphism
    >>> class Chicken(pfio.Relay):
    ...     def __init__(self):
    ...         pfio.Relay.__init__(self, 0)
    ...     def wobble(self):
    ...         self.turn_on()
    ...
    >>> chick1 = Chicken()
    >>> chick1.wobble()      # Turns on relay0 (connected to a robot chicken)

### Interrupts
Let's see what the InputFunctionMap does.

    >>> print(p.InputFunctionMap.__doc__)
    Maps inputs pins to functions.

        Use the register method to map inputs to functions.

        Each function is passed the interrupt bit map as a byte and the input
        port as a byte. The return value of the function specifies whether the
        wait_for_input loop should continue (True is continue).

        Register Parameters (*optional):
        input_num  - input pin number
        direction  - direction of change
                         IN_EVENT_DIR_ON
                         IN_EVENT_DIR_OFF
                         IN_EVENT_DIR_BOTH
        callback   - function to run when interrupt is detected
        board_num* - what PiFace digital board to check

        Example:
        def my_callback(interrupted_bit, input_byte):
             # if interrupted_bit = 0b00001000: pin 3 caused the interrupt
             # if input_byte = 0b10110111: pins 6 and 3 activated
            print(bin(interrupted_bit), bin(input_byte))
            return True  # keep waiting for interrupts
    
    >>>

And using it.

    >>> import pifacedigitalio as p
    >>> p.init()
    >>> pfd = p.PiFaceDigital()
    >>>
    >>> # create two functions
    >>> def toggle_led0(interrupt_bit, input_byte):
    ...     pfd.leds[0].toggle()
    ...     return True  # keep waiting for interrupts
    ...
    >>> def toggle_led7(interrupt_bit, input_byte):
    ...     pfd.leds[7].toggle()
    ...     return False  # stop waiting for interrupts (default behaviour)
    ...
    >>> ifm = p.InputFunctionMap()
    >>> ifm.register(
            input_num=0,
            direction=p.IN_EVENT_DIR_ON,
            callback=toggle_led0,
            board_num=0)
    >>> ifm.register(
            input_num=1,
            direction=p.IN_EVENT_DIR_ON,
            callback=toggle_led7,
            board_num=0)
    >>>
    >>> p.wait_for_input(ifm)  # will return after pressing input 1
