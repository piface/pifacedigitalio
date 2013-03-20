#!/usr/bin/env python
"""Provides I/O methods for interfacing with PiFace Digital (for Raspberry Pi)
Copyright (C) 2013 Thomas Preston <thomasmarkpreston@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
import ctypes
import posix
import select
import subprocess
from fcntl import ioctl
from asm_generic_ioctl import _IOW
from time import sleep
from datetime import datetime


# spi stuff requires Python 3
assert sys.version_info.major >= 3, __name__ + " is only supported on Python 3."


__pfdio_print_PREFIX = "PiFaceDigitalIO: " # prefix for pfdio messages

WRITE_CMD = 0
READ_CMD  = 1

# Register addresses
IODIRA   = 0x0 # I/O direction A
IODIRB   = 0x1 # I/O direction B
IPOLA    = 0x2 # I/O polarity A
IPOLB    = 0x3 # I/O polarity B
GPINTENA = 0x4 # interupt enable A
GPINTENB = 0x5 # interupt enable B
DEFVALA  = 0x6 # register default value A (interupts)
DEFVALB  = 0x7 # register default value B (interupts)
INTCONA  = 0x8 # interupt control A
INTCONB  = 0x9 # interupt control B
IOCON    = 0xa # I/O config (also 0xb)
GPPUA    = 0xc # port A pullups
GPPUB    = 0xd # port B pullups
INTFA    = 0xe # interupt flag A (where the interupt came from)
INTFB    = 0xf # interupt flag B
INTCAPA  = 0x10 # interupt capture A (value at interupt is saved here)
INTCAPB  = 0x11 # interupt capture B
GPIOA    = 0x12 # port A
GPIOB    = 0x13 # port B

# some easier to remember/read values
OUTPUT_PORT  = GPIOA
INPUT_PORT   = GPIOB
INPUT_PULLUP = GPPUB

# I/O config
# make a config byte like so:
BANK_OFF = 0x00 # addressing mode
BANK_ON  = 0x80
INT_MIRROR_ON  = 0x40 # interupt mirror (INTa|INTb)
INT_MIRROR_OFF = 0x00
SEQOP_OFF  = 0x20 # incrementing address pointer
SEQOP_ON   = 0x20
DISSLW_ON  = 0x10 # slew rate
DISSLW_OFF = 0x00
HAEN_ON    = 0x08 # hardware addressing
HAEN_OFF   = 0x00
ODR_ON  = 0x04 # open drain for interupts
ODR_OFF = 0x00
INTPOL_HIGH = 0x02 # interupt polarity
INTPOL_LOW  = 0x00

SPI_IOC_MAGIC = 107

MAX_BOARDS = 4

SPIDEV = '/dev/spidev0.0'
GPIO_INTERUPT_DEVICE = '/sys/devices/virtual/gpio/gpio25/'

spidev_fd = None


# custom exceptions
class InitError(Exception):
    pass

class InputDeviceError(Exception):
    pass

class RangeError(Exception):
    pass


# classes
class Item(object):
    """An item connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0, handler=None):
        self.pin_num = pin_num
        self.board_num = board_num
        if handler:
            self.handler = handler

    @property
    def handler(self):
        return sys.modules[__name__]

class InputItem(Item):
    """An input connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0, handler=None):
        super().__init__(pin_num, board_num, handler)

    @property
    def value(self):
        return 1 ^ self.handler.read_bit(self.pin_num, INPUT_PORT, self.board_num)

    @value.setter
    def value(self, data):
        raise InputDeviceError("You cannot set an input's values!")

class OutputItem(Item):
    """An output connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0, handler=None):
        super().__init__(pin_num, board_num, handler)

    @property
    def value(self):
        return self.handler.read_bit(self.pin_num, OUTPUT_PORT, self.board_num)

    @value.setter
    def value(self, data):
        return self.handler.write_bit(data, self.pin_num, OUTPUT_PORT, self.board_num)

    def turn_on(self):
        self.value = 1
    
    def turn_off(self):
        self.value = 0

    def toggle(self):
        self.value = not self.value

class LED(OutputItem):
    """An LED on PiFace Digital"""
    def __init__(self, led_num, board_num=0, handler=None):
        if led_num < 0 or led_num > 7:
            raise RangeError(
                    "Specified LED index (%d) out of range." % led_num)
        else:
            super().__init__(led_num, board_num, handler)

class Relay(OutputItem):
    """A relay on PiFace Digital"""
    def __init__(self, relay_num, board_num=0, handler=None):
        if relay_num < 0 or relay_num > 1:
            raise RangeError(
                    "Specified relay index (%d) out of range." % relay_num)
        else:
            super().__init__(relay_num, board_num, handler)

class Switch(InputItem):
    """A switch on PiFace Digital"""
    def __init__(self, switch_num, board_num=0, handler=None):
        if switch_num < 0 or switch_num > 3:
            raise RangeError(
                  "Specified switch index (%d) out of range." % switch_num)
        else:
            super().__init__(switch_num, board_num, handler)

class PiFaceDigital(object):
    """A single PiFace Digital board"""
    def __init__(self, board_num=0):
        self.board_num = board_num
        self.led    = [LED(i, board_num)    for i in range(8)]
        self.relay  = [Relay(i, board_num)  for i in range(2)]
        self.switch = [Switch(i, board_num) for i in range(4)]

class _spi_ioc_transfer(ctypes.Structure):                                      
    """SPI ioc transfer structure (from linux/spi/spidev.h)"""
    _fields_ = [
        ("tx_buf", ctypes.c_uint64),
        ("rx_buf", ctypes.c_uint64),
        ("len", ctypes.c_uint32),
        ("speed_hz", ctypes.c_uint32),
        ("delay_usecs", ctypes.c_uint16),
        ("bits_per_word", ctypes.c_uint8),
        ("cs_change", ctypes.c_uint8),
        ("pad", ctypes.c_uint32)]

class InputFunctionMap(list):
    """Maps inputs pins to callback functions.
    The callback function is passed a the input port as a byte 

    map parameters (*optional):
    index    - input pin number
    into     - direction of change (into 1 or 0, 0 is pressed, None=either)
    callback - function to run when interupt is detected
    board*   - what PiFace digital board to check

    def callback(input_port):
        print(bin(input_port)) # input_port = 0b11110111 <- pin 4 activated
    """
    def register(self, input_index, into, callback, board_index=0):
        self.append({'index' : input_index, 'into' : into,
            'callback' : callback, 'board' : board_index})


# functions
def init(init_board=True):
    """Initialises the PiFace Digital board"""
    global spidev_fd
    spidev_fd = posix.open(SPIDEV, posix.O_RDWR)

    if init_board:
        # set up each board
        ioconfig = BANK_OFF | INT_MIRROR_OFF | SEQOP_ON | DISSLW_OFF | \
                HAEN_ON | ODR_OFF | INTPOL_LOW

        for board_index in range(MAX_BOARDS):
            write(IOCON, ioconfig, board_index) # configure
            write(GPIOA, 0, board_index) # clear port A
            write(IODIRA, 0, board_index) # set port A as outputs
            write(IODIRB, 0xFF, board_index) # set port B as inputs
            write(GPPUB, 0xFF, board_index) # set port B pullups on

            # TODO: don't do this on external ports
            # check the outputs are being set (primitive board detection)
            # AR removed this test as it lead to flashing of outputs which 
            # could surprise users!
            #test_value = 0b10101010
            #write(OUTPUT_PORT, test_value)
            #if read(OUTPUT_PORT, board_num) != test_value:
            #    spi_handler = None
            #    raise InitError("The PiFace board could not be detected")

            # initialise outputs to 0
            #write(OUTPUT_PORT, 0, board_index)

def deinit():
    """Closes the spidev file descriptor"""
    global spidev_fd
    posix.close(spidev_fd)

def __pfdio_print(text):
    """Prints a string with the pfdio print prefix"""
    print("%s %s" % (__pfdio_print_PREFIX, text))

  
"""Some high level functions"""
def digital_read(pin_num, board_num=0):
    """Returns the status of the input pin specified.
    1 is active
    0 is inactive
    Note: This function is for familiarality with Arduino users
    """
    return read_bit(pin_num, INPUT_PORT, board_num) ^ 1 # inputs are

def digital_write(pin_num, value, board_num=0):
    """Writes the value specified to the output pin
    1 is active
    0 is inactive
    Note: This function is for familiarality with Arduino users
    """
    write_bit(value, pin_num, OUTPUT_PORT, board_num)

def digital_read_pullup(pin_num, board_num=0):
    return read_bit(pin_num, INPUT_PULLUP, board_num)

def digital_write_pullup(pin_num, value, board_num=0):
    write_bit(value, pin_num, INPUT_PULLUP, board_num)
"""END high level functions"""


def get_bit_mask(bit_num):
    """Translates a pin num to pin bit mask. First pin is pin0."""
    if bit_num > 7 or bit_num < 0:
        raise RangeError("Specified bit num (%d) out of range (0-7)." % \
                bit_num)
    else:
        return 1 << (bit_num)

def get_bit_num(bit_pattern):
    """Returns the lowest pin num from a given bit pattern"""
    bit_num = 0 # assume bit 0
    while (bit_pattern & 1) == 0:
        bit_pattern = bit_pattern >> 1
        bit_num += 1
        if bit_num > 7:
            bit_num = 0
            break
    
    return bit_num

def read_bit(bit_num, address, board_num=0):
    """Returns the bit specified from the address"""
    value = read(address, board_num)
    bit_mask = get_bit_mask(bit_num)
    return 1 if value & bit_mask else 0

def write_bit(value, bit_num, address, board_num=0):
    """Writes the value given to the bit specified"""
    bit_mask = get_bit_mask(bit_num)
    old_byte = read(address, board_num)
    # generate the new byte
    if value:
        new_byte = old_byte | bit_mask
    else:
        new_byte = old_byte & ~bit_mask
    write(address, new_byte, board_num)

def __get_device_opcode(board_num, read_write_cmd):
    """Returns the device opcode (as a byte)"""
    board_addr_pattern = (board_num << 1) & 0xE # 1 -> 0b0010, 3 -> 0b0110
    rw_cmd_pattern = read_write_cmd & 1 # make sure it's just 1 bit long
    return 0x40 | board_addr_pattern | rw_cmd_pattern

def read(address, board_num=0):
    """Reads from the address specified"""
    devopcode = __get_device_opcode(board_num, READ_CMD)
    op, addr, data = spisend((devopcode, address, 0)) # data byte is not used
    return data

def write(address, data, board_num=0):
    """Writes data to the address specified"""
    devopcode = __get_device_opcode(board_num, WRITE_CMD)
    op, addr, data = spisend((devopcode, address, data))

def spisend(bytes_to_send):
    """Sends bytes via the SPI bus"""
    global spidev_fd
    if spidev_fd == None:
        raise InitError("Before spisend(), call init().")

    # make some buffer space to store reading/writing
    write_bytes = bytes(bytes_to_send)
    wbuffer = ctypes.create_string_buffer(write_bytes, len(write_bytes))
    rbuffer = ctypes.create_string_buffer(len(bytes_to_send))

    # create the spi transfer struct
    transfer = _spi_ioc_transfer(
        tx_buf=ctypes.addressof(wbuffer),
        rx_buf=ctypes.addressof(rbuffer),
        len=ctypes.sizeof(wbuffer))

    # send the spi command (with a little help from asm-generic
    iomsg = _IOW(SPI_IOC_MAGIC, 0, ctypes.c_char*ctypes.sizeof(transfer))
    ioctl(spidev_fd, iomsg, ctypes.addressof(transfer))
    return ctypes.string_at(rbuffer, ctypes.sizeof(rbuffer))


# interupts
def wait_for_input(input_func_map=None, loop=False, timeout=None):
    """Waits for an input to be pressed (using interups rather than polling)

    Paramaters:
    input_func_map - An InputFunctionMap object describing callbacks
    loop           - If true, keep checking interupt status
    timeout        - How long we should wait before giving up and exiting the
                     function
    """
    enable_interupts()

    # set up epoll (can't do it in enable_interupts for some reason)
    gpio25 = open(GPIO_INTERUPT_DEVICE+'value', 'r')
    epoll = select.epoll()
    epoll.register(gpio25, select.EPOLLIN | select.EPOLLET)

    while True:
        # wait here until input
        try:
            events = epoll.poll(timeout) if timeout else epoll.poll()
        except KeyboardInterrupt:
            epoll.close()
            disable_interupts() # more graceful
            raise

        if len(events) <= 0:
            epoll.close()
            disable_interupts()
            return

        if input_func_map:
            call_mapped_input_functions(input_func_map)

        if not loop:
            epoll.close()
            disable_interupts()
            return
 
def call_mapped_input_functions(input_func_map):
    for board_i in range(MAX_BOARDS):
        this_board_ifm = [m for m in input_func_map if m['board'] == board_i]
        
        # read the interupt status of this PiFace board
        int_bit = read(INTFB, board_i)
        if int_bit == 0:
            continue # The interupt has not been flagged on this board
        int_bit_num = get_bit_num(int_bit)
        int_byte = read(INTCAPB, board_i)
        into = (int_bit & int_byte) >> int_bit_num # bit changed into (0/1)
        
        # for each mapping (on this board) see if we have a callback
        for mapping in this_board_ifm:
            if int_bit_num == mapping['index'] and \
                (mapping['into'] == None or into == mapping['into']):
                mapping['callback'](int_byte)
                return # one at a time

def clear_interupts():
    """Clears the interupt flags by reading the capture register on all boards"""
    for i in range(MAX_BOARDS):
        read(INTCAPB, i)

def enable_interupts():
    for board_index in range(MAX_BOARDS):
        write(GPINTENB, 0xff, board_index)

    # access quick2wire-gpio-admin for gpio pin twiddling
    try:
        subprocess.check_call(["gpio-admin", "export", "25"])
    except subprocess.CalledProcessError as e:
        if e.returncode != 4: # we can ignore 4 (gpio25 is already up)
            raise e

    # we're only interested in the falling edges of this file (1 -> 0)
    with open(GPIO_INTERUPT_DEVICE+'edge', 'w') as gpio25edge:
        gpio25edge.write('falling')

def disable_interupts():
    with open(GPIO_INTERUPT_DEVICE+'edge', 'w') as gpio25edge:
        gpio25edge.write('none')

    try:
        subprocess.check_call(["gpio-admin", "unexport", "25"])
    except subprocess.CalledProcessError as e:
        if e.returncode != 4: # we can ignore 4 (gpio25 is already down)
            raise e

    for board_index in range(MAX_BOARDS):
        write(GPINTENB, 0, board_index) # disable the interupt
