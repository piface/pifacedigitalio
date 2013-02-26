#!/usr/bin/env python
"""
pifacedigitalio.py
Provides I/O methods for interfacing with PiFace Digital (on the Raspberry Pi)
Copyright (C) 2013 Thomas Preston <thomasmarkpreston@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
from time import sleep
from datetime import datetime

import sys
import spipy


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
    """An item connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0, handler=None):
        self.pin_num = pin_num
        self.board_num = board_num
        if handler:
            self.handler = handler

    def _get_handler(self):
        return sys.modules[__name__]

    handler = property(_get_handler, None)

class InputItem(Item):
    """An input connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0, handler=None):
        Item.__init__(self, pin_num, board_num, handler)

    def _get_value(self):
        return self.handler.digital_read(self.pin_num, self.board_num)

    def _set_value(self, data):
        raise InputDeviceError("You cannot set an input's values!")

    value = property(_get_value, _set_value)

class OutputItem(Item):
    """An output connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0, handler=None):
        self.current = 0
        Item.__init__(self, pin_num, board_num, handler)

    def _get_value(self):
        return self.current

    def _set_value(self, data):
        self.current = data
        return self.handler.digital_write(self.pin_num, data, self.board_num)

    value = property(_get_value, _set_value)

    def turn_on(self):
        self.value = 1
    
    def turn_off(self):
        self.value = 0

    def toggle(self):
        self.value = not self.value

class LED(OutputItem):
    """An LED on PiFace Digital"""
    def __init__(self, led_number, board_num=0, handler=None):
        if led_number < 0 or led_number > 7:
            raise LEDRangeError(
                    "Specified LED index (%d) out of range." % led_number)
        else:
            OutputItem.__init__(self, led_number, board_num, handler)

class Relay(OutputItem):
    """A relay on PiFace Digital"""
    def __init__(self, relay_number, board_num=0, handler=None):
        if relay_number < 0 or relay_number > 1:
            raise RelayRangeError(
                    "Specified relay index (%d) out of range." % relay_number)
        else:
            OutputItem.__init__(self, relay_number, board_num, handler)

class Switch(InputItem):
    """A switch on PiFace Digital"""
    def __init__(self, switch_number, board_num=0, handler=None):
        if switch_number < 0 or switch_number > 3:
            raise SwitchRangeError(
                  "Specified switch index (%d) out of range." % switch_number)
        else:
            InputItem.__init__(self, switch_number, board_num, handler)

class PiFaceDigital(object):
    """A single PiFace Digital board"""
    def __init__(self, board_num=0):
        self.board_num = board_num

        self.led = list()
        for i in range(8):
            self.led.append(LED(i, board_num))

        self.relay = list()
        for i in range(2):
            self.relay.append(Relay(i, board_num))

        self.switch = list()
        for i in range(4):
            self.switch.append(Switch(i, board_num))


# functions
def get_spi_handler():
    return spipy.SPI(0,0) # spipy.SPI(X,Y) is /dev/spidevX.Y

def init(init_ports=True):
    """Initialises the PiFace"""
    if VERBOSE_MODE:
         __pfdio_print("initialising SPI")

    global spi_handler
    try:
        spi_handler = get_spi_handler()
    except spipy.error as error:
        raise InitError(error)

    if init_ports:
        for board_index in range(8):
            # set up the ports
            write(IOCON,  8, board_index)    # enable hardware addressing
            write(GPIOA,  0, board_index)    # set port A on
            write(IODIRA, 0, board_index)    # set port A as outputs
            write(IODIRB, 0xFF, board_index) # set port B as inputs
            #write(GPIOA,  0xFF, board_index) # set port A on
            #write(GPIOB,  0xFF, board_index) # set port B on
            #write(GPPUA,  0xFF, board_index) # set port A pullups on
            write(GPPUB,  0xFF, board_index) # set port B pullups on

            # check the outputs are being set (primitive board detection)
            # AR removed this test as it lead to flashing of outputs which 
            # could surprise users!
            #test_value = 0b10101010
            #write_output(test_value)
            #if read_output() != test_value:
            #    spi_handler = None
            #    raise InitError("The PiFace board could not be detected")

            # initialise outputs to 0
            write_output(0, board_index)

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
    board_addr_pattern = (board_num << 1) & 0xE # 1 -> 0b0010, 3 -> 0b0110
    rw_cmd_pattern = read_write_cmd & 1 # make sure it's just 1 bit long
    return 0x40 | board_addr_pattern | rw_cmd_pattern

def read(port, board_num=0):
    """Reads from the port specified"""
    devopcode = __get_device_opcode(board_num, READ_CMD)
    operation, port, data = send(devopcode, port, 0) # data byte is not used
    return (port, data)

def write(port, data, board_num=0):
    """Writes data to the port specified"""
    devopcode = __get_device_opcode(board_num, WRITE_CMD)
    operation, port, data = send(devopcode, port, data)
    return (port, data)

def send(devopcode, port, data):
    """Sends three bytes via the SPI bus"""
    if spi_handler == None:
        raise InitError("The pfdio module has not yet been initialised. Before send(), call init().")
    else:
        return spi_handler.transfer(devopcode, port, data)


def test_method():
    # write pin 1 high/low
    digital_write(0,1)
    sleep(2)
    digital_write(0,0)

if __name__ == "__main__":
    init()
    test_method()
    deinit()
