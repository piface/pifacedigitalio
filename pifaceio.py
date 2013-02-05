#!/usr/bin/env python
"""
pfio.py
Provides I/O methods for interfacing with the RaspberryPi interface (piface)

piface has two ports (input/output) each with eight pins with several
peripherals connected for interacting with the raspberry pi
"""
from time import sleep
from datetime import datetime

import sys
import spi


VERBOSE_MODE = False # toggle verbosity
__pfio_print_PREFIX = "PFIO: " # prefix for pfio messages

# SPI operations
WRITE_CMD = 0x40
READ_CMD  = 0x41

# Port configuration
IODIRA = 0x00 # I/O direction A
IODIRB = 0x01 # I/O direction B
IOCON  = 0x0A # I/O config
GPIOA  = 0x12 # port A
GPIOB  = 0x13 # port B
GPPUA  = 0x0C # port A pullups
GPPUB  = 0x0D # port B pullups
OUTPUT_PORT = GPIOA
INPUT_PORT  = GPIOB
INPUT_PULLUPS = GPPUB

# piface peripheral pin numbers
# each peripheral is connected to an I/O pin
# some pins are connected to many peripherals
# outputs
PH_PIN_LED_1 = 1
PH_PIN_LED_2 = 2
PH_PIN_LED_3 = 3
PH_PIN_LED_4 = 4
PH_PIN_LED_5 = 5
PH_PIN_LED_6 = 6
PH_PIN_LED_7 = 7
PH_PIN_LED_8 = 8
PH_PIN_RELAY_1 = 1
PH_PIN_RELAY_2 = 2
# inputs
PH_PIN_SWITCH_1 = 1
PH_PIN_SWITCH_2 = 2
PH_PIN_SWITCH_3 = 3
PH_PIN_SWITCH_4 = 4

spi_handler = None

spi_visualiser_section = None # for the emulator spi visualiser


# custom exceptions
class InitError(Exception):
    pass

class InputDeviceError(Exception):
    pass

class PinRangeError(Exception):
    pass


# classes
class Item(object):
    """An item connected to a pin on the RaspberryPi"""
    def __init__(self, pin_number, handler=None):
        self.pin_number = pin_number

    def _get_handler(self):
        return sys.modules[__name__]

    handler = property(_get_handler, None)

class InputItem(Item):
    """An input connected to a pin on the RaspberryPi"""
    def _get_value(self):
        return self._handler().digital_read(self.pin_number)

    def _set_value(self, data):
        raise InputDeviceError("You cannot set an input's values!")

    value = property(_get_value, _set_value)

class OutputItem(Item):
    """An output connected to a pin on the RaspberryPi"""
    def __init__(self, pin_number, handler=None):
        self.current = 0
        Item.__init__(self, pin_number, handler)

    def _get_value(self):
        return self.current

    def _set_value(self, data):
        self.current = data
        return self.handler.digital_write(self.pin_number, data)

    value = property(_get_value, _set_value)

    def turn_on(self):
        self.value = 1
    
    def turn_off(self):
        self.value = 0

    def toggle(self):
        self.value = not self.value

class LED(OutputItem):
    """An LED on the RaspberryPi"""
    def __init__(self, led_number, handler=None):
        if led_number == 1:
            pin_number = PH_PIN_LED_1
        elif led_number == 2:
            pin_number = PH_PIN_LED_2
        elif led_number == 3:
            pin_number = PH_PIN_LED_3
        elif led_number == 4:
            pin_number = PH_PIN_LED_4
        elif led_number == 5:
            pin_number = PH_PIN_LED_5
        elif led_number == 6:
            pin_number = PH_PIN_LED_6
        elif led_number == 7:
            pin_number = PH_PIN_LED_7
        else:
            pin_number = PH_PIN_LED_8

        OutputItem.__init__(self, pin_number, handler)

class Relay(OutputItem):
    """A relay on the RaspberryPi"""
    def __init__(self, relay_number, handler=None):
        if relay_number == 1:
            pin_number = PH_PIN_RELAY_1
        else:
            pin_number = PH_PIN_RELAY_2

        OutputItem.__init__(self, pin_number, handler)

class Switch(InputItem):
    """A switch on the RaspberryPi"""
    def __init__(self, switch_number, handler=None):
        if switch_number == 1:
            switch_number = PH_PIN_SWITCH_1
        elif switch_number == 2:
            switch_number = PH_PIN_SWITCH_2
        elif switch_number == 3:
            switch_number = PH_PIN_SWITCH_3
        else:
            switch_number = PH_PIN_SWITCH_4

        InputItem.__init__(self, switch_number, handler)


# functions
def get_spi_handler():
    return spi.SPI(0,0) # spi.SPI(X,Y) is /dev/spidevX.Y

def init():
    """Initialises the PiFace"""
    if VERBOSE_MODE:
         #print "PIFO: initialising SPI mode, reading data, reading length . . . \n"
         __pfio_print("initialising SPI")

    global spi_handler
    try:
        spi_handler = get_spi_handler()
    except spi.error as error:
        raise InitError(error)

    # set up the ports
    write(IOCON,  8)    # enable hardware addressing
    write(GPIOA,  0x00) # set port A on
    write(IODIRA, 0)    # set port A as outputs
    write(IODIRB, 0xFF) # set port B as inputs
    #write(GPIOA,  0xFF) # set port A on
    #write(GPIOB,  0xFF) # set port B on
    #write(GPPUA,  0xFF) # set port A pullups on
    write(GPPUB,  0xFF) # set port B pullups on

    # check the outputs are being set (primitive board detection)
#AR removed this test as it lead to flashing of outputs which 
# could surprise users!

#    test_value = 0b10101010
#    write_output(test_value)
#    if read_output() != test_value:
#        spi_handler = None
#        raise InitError("The PiFace board could not be detected")

    # initialise all outputs to 0
    write_output(0)

def deinit():
    """Deinitialises the PiFace"""
    global spi_handler
    if spi_handler:
        spi_handler.close()
        spi_handler = None

def __pfio_print(text):
    """Prints a string with the pfio print prefix"""
    print "%s %s" % (__pfio_print_PREFIX, text)

def get_pin_bit_mask(pin_number):
    """Translates a pin number to pin bit mask. First pin is pin0."""
    if pin_number > 7 or pin_number < 0:
        raise PinRangeError("Specified pin number (%d) out of range." % pin_number)
    else:
        return 1 << (pin_number)

def get_pin_number(bit_pattern):
    """Returns the lowest pin number from a given bit pattern"""
    pin_number = 0 # assume pin 0
    while (bit_pattern & 1) == 0:
        bit_pattern = bit_pattern >> 1
        pin_number += 1
        if pin_number > 7:
            pin_number = 0
            break
    
    return pin_number

def byte_cat(items):
    """
    Returns a value comprised of the concatenation of the given hex values
    Example: (0x41, 0x16, 0x01) -> 0x411601
    """
    items = list(items)
    items.reverse()
    cauldron = 0
    for i in range(len(items)):
        cauldron ^= items[i] << (i * 8)
    return cauldron

def digital_write(pin_number, value):
    """Writes the value given to the pin specified"""
    if VERBOSE_MODE:
        __pfio_print("digital write start")

    pin_bit_mask = get_pin_bit_mask(pin_number)

    if VERBOSE_MODE:
        __pfio_print("pin bit mask: %s" % bin(pin_bit_mask))

    old_pin_values = read_output()

    if VERBOSE_MODE:
        __pfio_print("old pin values: %s" % bin(old_pin_values))

    # generate the 
    if value:
        new_pin_values = old_pin_values | pin_bit_mask
    else:
        new_pin_values = old_pin_values & ~pin_bit_mask

    if VERBOSE_MODE:
        __pfio_print("new pin values: %s" % bin(new_pin_values))

    write_output(new_pin_values)

    if VERBOSE_MODE:
        __pfio_print("digital write end")

def digital_read(pin_number):
    """Returns the value of the pin specified"""
    current_pin_values = read_input()
    pin_bit_mask = get_pin_bit_mask(pin_number)

    result = current_pin_values & pin_bit_mask

    # is this correct? -thomas preston
    if result:
        return 1
    else:
        return 0

def digital_write_pullup(pin_number, value):
    """Writes the pullup value given to the pin specified"""
    if VERBOSE_MODE:
        __pfio_print("digital write pullup start")

    pin_bit_mask = get_pin_bit_mask(pin_number)

    if VERBOSE_MODE:
        __pfio_print("pin bit mask: %s" % bin(pin_bit_mask))

    old_pin_values = read_pullup()

    if VERBOSE_MODE:
        __pfio_print("old pin values: %s" % bin(old_pin_values))

    # generate the 
    if value:
        new_pin_values = old_pin_values | pin_bit_mask
    else:
        new_pin_values = old_pin_values & ~pin_bit_mask

    if VERBOSE_MODE:
        __pfio_print("new pin values: %s" % bin(new_pin_values))

    write_pullups(new_pin_values)

    if VERBOSE_MODE:
        __pfio_print("digital write end")

"""
Some wrapper functions so the user doesn't have to deal with
ugly port variables
"""
def read_output():
    """Returns the values of the output pins"""
    port, data = read(OUTPUT_PORT)
    return data

def read_input():
    """Returns the values of the input pins"""
    port, data = read(INPUT_PORT)
    # inputs are active low, but the user doesn't need to know this...
    return data ^ 0xff 

def read_pullups():
    """Reads value of pullup registers"""
    port, data = read(INPUT_PULLUPS)
    return data

def write_pullups(data):
    port, data = write(INPUT_PULLUPS, data)
    return data

def write_output(data):
    """Writed the values of the output pins"""
    port, data = write(OUTPUT_PORT, data)
    return data

"""
def write_input(data):
    " ""Writes the values of the input pins"" "
    port, data = write(INPUT_PORT, data)
    return data
"""


def read(port):
    """Reads from the port specified"""
    # data byte is padded with 1's since it isn't going to be used
    operation, port, data = send([(READ_CMD, port, 0xff)])[0] # send is expecting and returns a list
    return (port, data)

def write(port, data):
    """Writes data to the port specified"""
    #print "writing"
    operation, port, data = send([(WRITE_CMD, port, data)])[0] # send is expecting and returns a list
    return (port, data)


def send(spi_commands, custom_spi=False):
    """Sends a list of spi commands to the PiFace"""
    if spi_handler == None:
        raise InitError("The pfio module has not yet been initialised. Before send(), call init().")
    # a place to store the returned values for each transfer
    returned_values_list = list() 

    # datum is an array of three bytes
    for cmd, port, data in spi_commands:
        datum_tx = byte_cat((cmd, port, data))
        if VERBOSE_MODE:
            __pfio_print("transfering data: 0x%06x" % datum_tx)

        # transfer the data string
        returned_values = spi_handler.transfer("%06x" % datum_tx, 3)
        datum_rx = byte_cat(returned_values)

        returned_values_list.append(returned_values)

        if VERBOSE_MODE:
            __pfio_print("SPI module returned: 0x%06x" % datum_rx)

        # if we are visualising, add the data to the emulator visualiser
        global spi_visualiser_section
        if spi_visualiser_section:
            time = datetime.now()
            timestr = "%d:%d:%d.%d" % (time.hour, time.minute, time.second, time.microsecond)
            datum_tx = byte_cat((cmd, port, data)) # recalculate since the transfer changes it
            #print "writing to spi_liststore: %s" % str((timestr, hex(datum_tx), hex(datum_rx)))
            spi_visualiser_section.add_spi_log(timestr, datum_tx, datum_rx, custom_spi)

    return returned_values_list


def test_method():
    digital_write(1,1) # write pin 1 high
    sleep(2)
    digital_write(1,0) # write pin 1 low

if __name__ == "__main__":
    init()
    test_method()
    deinit()
