#!/usr/bin/env python
"""
pifacedigitalio.py
Provides I/O methods for interfacing with PiFace Digital (on the Raspberry Pi)

PiFace has two ports (input/output) each with eight pins with several
peripherals connected for interacting with the Raspberry Pi
"""
from time import sleep
from datetime import datetime

import sys
import spi


VERBOSE_MODE = False # toggle verbosity
__pfdio_print_PREFIX = "PiFaceDigitalIO: " # prefix for pfdio messages

# SPI operations
WRITE_CMD = 0
READ_CMD  = 1

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

spi_handler = None

spi_visualiser_section = None # for the emulator spi visualiser


# custom exceptions
class InitError(Exception):
    pass

class InputDeviceError(Exception):
    pass

class PinRangeError(Exception):
    pass

class LEDRangeError(Exception):
    pass

class RelayRangeError(Exception):
    pass

class SwitchRangeError(Exception):
    pass


# classes
class Item(object):
    """An item connected to a pin on the RaspberryPi"""
    def __init__(self, pin_number, handler=None):
        self.pin_number = pin_number
        if handler:
            self.handler = handler

    def _get_handler(self):
        return sys.modules[__name__]

    handler = property(_get_handler, None)

class InputItem(Item):
    """An input connected to a pin on the RaspberryPi"""
    def __init__(self, pin_number, handler=None):
        Item.__init__(self, pin_number, handler)

    def _get_value(self):
        return self.handler.digital_read(self.pin_number)

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
        if led_number < 0 or led_number > 7:
            raise LEDRangeError(
                    "Specified LED index (%d) out of range." % led_number)
        else:
            OutputItem.__init__(self, led_number, handler)

class Relay(OutputItem):
    """A relay on the RaspberryPi"""
    def __init__(self, relay_number, handler=None):
        if relay_number < 0 or relay_number > 1:
            raise RelayRangeError(
                    "Specified relay index (%d) out of range." % relay_number)
        else:
            OutputItem.__init__(self, relay_number, handler)

class Switch(InputItem):
    """A switch on the RaspberryPi"""
    def __init__(self, switch_number, handler=None):
        if switch_number < 0 or switch_number > 3:
            raise SwitchRangeError(
                  "Specified switch index (%d) out of range." % switch_number)
        else:
            InputItem.__init__(self, switch_number, handler)


# functions
def get_spi_handler():
    return spi.SPI(0,0) # spi.SPI(X,Y) is /dev/spidevX.Y

def init(init_ports=True):
    """Initialises the PiFace"""
    if VERBOSE_MODE:
         __pfdio_print("initialising SPI")

    global spi_handler
    try:
        spi_handler = get_spi_handler()
    except spi.error as error:
        raise InitError(error)

    if init_ports:
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
        # AR removed this test as it lead to flashing of outputs which 
        # could surprise users!
        #test_value = 0b10101010
        #write_output(test_value)
        #if read_output() != test_value:
        #    spi_handler = None
        #    raise InitError("The PiFace board could not be detected")

        # initialise all outputs to 0
        write_output(0)

def deinit():
    """Deinitialises the PiFace"""
    global spi_handler
    if spi_handler:
        spi_handler.close()
        spi_handler = None

def __pfdio_print(text):
    """Prints a string with the pfdio print prefix"""
    print "%s %s" % (__pfdio_print_PREFIX, text)

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

def digital_write(pin_number, value, board_num=0):
    """Writes the value given to the pin specified"""
    if VERBOSE_MODE:
        __pfdio_print("digital write start")

    pin_bit_mask = get_pin_bit_mask(pin_number)

    if VERBOSE_MODE:
        __pfdio_print("pin bit mask: %s" % bin(pin_bit_mask))

    old_pin_values = read_output(board_num)

    if VERBOSE_MODE:
        __pfdio_print("old pin values: %s" % bin(old_pin_values))

    # generate the 
    if value:
        new_pin_values = old_pin_values | pin_bit_mask
    else:
        new_pin_values = old_pin_values & ~pin_bit_mask

    if VERBOSE_MODE:
        __pfdio_print("new pin values: %s" % bin(new_pin_values))

    write_output(new_pin_values, board_num)

    if VERBOSE_MODE:
        __pfdio_print("digital write end")

def digital_read(pin_number, board_num=0):
    """Returns the value of the pin specified"""
    current_pin_values = read_input(board_num)
    pin_bit_mask = get_pin_bit_mask(pin_number)

    result = current_pin_values & pin_bit_mask

    # is this correct? -thomas preston
    if result:
        return 1
    else:
        return 0

def digital_write_pullup(pin_number, value, board_num=0):
    """Writes the pullup value given to the pin specified"""
    if VERBOSE_MODE:
        __pfdio_print("digital write pullup start")

    pin_bit_mask = get_pin_bit_mask(pin_number)

    if VERBOSE_MODE:
        __pfdio_print("pin bit mask: %s" % bin(pin_bit_mask))

    old_pin_values = read_pullup(board_num)

    if VERBOSE_MODE:
        __pfdio_print("old pin values: %s" % bin(old_pin_values))

    # generate the 
    if value:
        new_pin_values = old_pin_values | pin_bit_mask
    else:
        new_pin_values = old_pin_values & ~pin_bit_mask

    if VERBOSE_MODE:
        __pfdio_print("new pin values: %s" % bin(new_pin_values))

    write_pullups(new_pin_values, board_num)

    if VERBOSE_MODE:
        __pfdio_print("digital write end")

"""
Some wrapper functions so the user doesn't have to deal with
ugly port variables
"""
def read_output(board_num=0):
    """Returns the values of the output pins"""
    port, data = read(OUTPUT_PORT, board_num)
    return data

def read_input(board_num=0):
    """Returns the values of the input pins"""
    port, data = read(INPUT_PORT, board_num)
    # inputs are active low, but the user doesn't need to know this...
    return data ^ 0xff 

def read_pullups(board_num=0):
    """Reads value of pullup registers"""
    port, data = read(INPUT_PULLUPS, board_num)
    return data

def write_pullups(data, board_num=0):
    port, data = write(INPUT_PULLUPS, data, board_num)
    return data

def write_output(data, board_num=0):
    """Writed the values of the output pins"""
    port, data = write(OUTPUT_PORT, data, board_num)
    return data

"""
def write_input(data):
    " ""Writes the values of the input pins"" "
    port, data = write(INPUT_PORT, data)
    return data
"""

def __get_device_opcode(board_num, read_write_cmd):
    """Returns the device opcode (as a byte)"""
    board_addr_pattern = (1 << board_num) & 0xE # 1 -> 0b0000, 2 -> 0b0010
    rw_cmd_pattern = read_write_cmd & 1 # make sure it's just 1 bit long
    return 0x40 | board_addr_pattern | rw_cmd_pattern

def read(port, board_num=0):
    """Reads from the port specified"""
    # data byte is padded with 1's since it isn't going to be used
    devopcode = __get_device_opcode(board_num, READ_CMD)
    operation, port, data = send([(devopcode, port, 0xff)])[0] # send is expecting and returns a list
    return (port, data)

def write(port, data, board_num=0):
    """Writes data to the port specified"""
    devopcode = __get_device_opcode(board_num, WRITE_CMD)
    operation, port, data = send([(devopcode, port, data)])[0] # send is expecting and returns a list
    return (port, data)

def send(spi_commands, custom_spi=False):
    """Sends a list of spi commands to the PiFace"""
    if spi_handler == None:
        raise InitError("The pfdio module has not yet been initialised. Before send(), call init().")
    # a place to store the returned values for each transfer
    returned_values_list = list() 

    # datum is an array of three bytes
    for cmd, port, data in spi_commands:
        datum_tx = byte_cat((cmd, port, data))
        if VERBOSE_MODE:
            __pfdio_print("transfering data: 0x%06x" % datum_tx)

        # transfer the data string
        returned_values = spi_handler.transfer("%06x" % datum_tx, 3)
        datum_rx = byte_cat(returned_values)

        returned_values_list.append(returned_values)

        if VERBOSE_MODE:
            __pfdio_print("SPI module returned: 0x%06x" % datum_rx)

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
