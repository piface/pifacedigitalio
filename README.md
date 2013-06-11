pifacedigitalio
===============

The PiFace Digital Input/Output module.

The PiFace Digital IO module uses **Python 3** and is incompatible with 
Python 2. *You have to type `python3` instead of `python` in the command line.*

About
=====
PiFace Digital has eight inputs, eight outputs, eight LED's, two relays and
four switches.

### Outputs
The eight output pins are located at the top of the board (near the LED's). The
outputs are open collectors; they can be thought of as switches connecting to
ground. This offers greater flexibility since the PiFace can control devices
that operate using different voltages. The ninth pin provides 5V for connecting
circuits to.

An example circuit is (**R**esistor, **L**ED, **O**utput pin, **5**V pin):
<pre>
 +-R-L--+
OOOOOOOO5
</pre>
(Sorry about the ASCII art)

The LED's are connected in parallel to each of the outputs. This means that
when you set output pin 4 high, LED 4 illuminates.

The two Relays are connected in paralley to output pins 0 and 1 respectively.
When you set output pin 0 high, LED 0 illuminated and Relay 0 activates. When
activated, the relay bridges the top and middle pins. When deactivated the
bottom two are connected.

<pre>
Relay activated
[Top Pin   ]
[Common    ]
 Bottom Pin

Relay Deactivated
 Top Pin
[Common    ]
[Bottom Pin]
</pre>

### Inputs
The eight input pins detect a connection to ground (provided as the ninth pin).
The four switches are connected in parallel to the first four input pins. The
inputs are *pulled up* to 5V. This can be turned off so that the inputs float.

Installation
============
    $ sudo ./install.sh

You may need to reboot for interrupts to work.


Examples
=======
### Basic usage
Set up:

    $ python3
    >>> import pifacedigitalio as p
    >>> p.init()       # initialises the PiFace Digital board 
    >>> p.init(False)  # same as above w/out resetting ports

Playing with PiFace Digital:

    >>> pfd = p.PiFaceDigital() # creates a PiFace Digtal object
    >>>
    >>> pfd.leds[1].turn_on()    # turn on the second LED
    >>> pfd.leds[2].toggle()     # toggle third LED
    >>> pfd.switches[3].value    # check the status of switch3
    0
    >>> pfd.relays[0].value = 1  # turn on the first relay
    >>>
    >>> pfd.output_pins[6].value = 1
    >>> pfd.output_pins[6].turn_off()
    >>>
    >>> pfd.input_pins[6].value
    0
    >>>
    >>> pfd.output_port.all_off()
    >>> pfd.output_port.value = 0xAA
    >>> pfd.output_port.toggle()
    >>>
    >>> bin(pfd.input_port.value)  # with the fourth switch pressed
    '0b1000'

You can talk to the components directly:

    >>> led0 = p.LED(0)  # create an LED object (pin0, board0)
    >>> led0.turn_on()   # turn on the LED
    >>> led0.value = 1   # turn on the LED
    >>>
    >>> led3_2 = p.LED(3, 2)  # create an LED object (pin3, board2)
    >>> led3_2.turn_on()      # turn on the LED
    >>>
    >>> switch2 = p.Switch(2) # create a Switch object (pin2, board0)
    >>> switch2.value         # is the switch pressed?
    0

Some functions you might want to use if objects aren't your thing (though, you
should probably be looking at [pifacecommon](https://github.com/piface/pifacecommon)
instead):

    >>> p.digital_write(0, 1)    # writes pin0 (board0) high
    >>> p.digital_write(5, 1, 2) # writes pin5 on board2 high
    >>> p.digital_read(4)        # reads pin4 (on board0)
    0
    >>> p.digital_read(2, 3)     # reads pin2 (on board3)
    1

### Polymorphism
    >>> class Chicken(pifacedigitalio.Relay):
    ...     def __init__(self):
    ...         super().__init__(0)
    ...     def wobble(self):
    ...         self.turn_on()
    ...
    >>> chick1 = Chicken()
    >>> chick1.wobble()      # Turns on relay0 (connected to a robot chicken)

### Interrupts
Let's see what the pifacecommon.InputFunctionMap does.

    $ python3
    >>> import pifacecommon
    >>> print(pifacecommon.InputFunctionMap.__doc__)
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

    $ python3
    >>> import pifacecommon
    >>> import pifacedigitalio
    >>>
    >>> pifacedigitalio.init()
    >>> pfd = pifacedigitalio.PiFaceDigital()
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
    >>> ifm = pifacecommon.InputFunctionMap()
    >>>
    >>> # when switch 0 (input0) is pressed, run toggle_led0
    >>> ifm.register(
            input_num=0,
            direction=pifacecommon.IN_EVENT_DIR_ON,
            callback=toggle_led0,
            board_num=0)  # optional
    >>>
    >>> # when switch 1 (input1) is un-pressed, run toggle_led7
    >>> ifm.register(
            input_num=1,
            direction=pifacecommon.IN_EVENT_DIR_OFF,
            callback=toggle_led7)
    >>>
    >>> pifacedigitalio.wait_for_input(ifm)  # returns after un-pressing switch1
