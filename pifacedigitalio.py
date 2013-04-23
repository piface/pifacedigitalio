#!/usr/bin/env python3
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
import select
import subprocess
import pifacecommon as pfcom

# /dev/spidev<bus>.<chipselect>
SPI_BUS = 0
SPI_CHIP_SELECT = 0

# some easier to remember/read values
OUTPUT_PORT = pfcom.GPIOA
INPUT_PORT = pfcom.GPIOB
INPUT_PULLUP = pfcom.GPPUB

MAX_BOARDS = 4

GPIO_INTERUPT_DEVICE = '/sys/devices/virtual/gpio/gpio25/'


class InitError(Exception):
    pass


class InputDeviceError(Exception):
    pass


class RangeError(Exception):
    pass


class NoPiFaceDigitalDetectedError(Exception):
    pass


class Item(object):
    """An item connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0):
        self.pin_num = pin_num
        if board_num < 0 or board_num >= MAX_BOARDS:
            raise RangeError(
                "Specified board index (%d) out of range." % board_num
            )
        else:
            self.board_num = board_num

    @property
    def handler(self):
        return pfcom


class InputItem(Item):
    """An input connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0):
        super().__init__(pin_num, board_num)

    @property
    def value(self):
        return 1 ^ self.handler.read_bit(self.pin_num, INPUT_PORT, self.board_num)

    @value.setter
    def value(self, data):
        raise InputDeviceError("You cannot set an input's values!")


class OutputItem(Item):
    """An output connected to a pin on PiFace Digital"""
    def __init__(self, pin_num, board_num=0):
        super().__init__(pin_num, board_num)

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
    def __init__(self, led_num, board_num=0):
        if led_num < 0 or led_num > 7:
            raise RangeError(
                "Specified LED index (%d) out of range." % led_num)
        else:
            super().__init__(led_num, board_num)


class Relay(OutputItem):
    """A relay on PiFace Digital"""
    def __init__(self, relay_num, board_num=0):
        if relay_num < 0 or relay_num > 1:
            raise RangeError(
                "Specified relay index (%d) out of range." % relay_num)
        else:
            super().__init__(relay_num, board_num)


class Switch(InputItem):
    """A switch on PiFace Digital"""
    def __init__(self, switch_num, board_num=0):
        if switch_num < 0 or switch_num > 3:
            raise RangeError(
                "Specified switch index (%d) out of range." % switch_num)
        else:
            super().__init__(switch_num, board_num)


class PiFaceDigital(object):
    """A single PiFace Digital board"""
    def __init__(self, board_num=0):
        self.board_num = board_num
        self.input_pins = [InputItem(i, board_num) for i in range(8)]
        self.output_pins = [OutputItem(i, board_num) for i in range(8)]
        self.leds = [LED(i, board_num) for i in range(8)]
        self.relays = [Relay(i, board_num) for i in range(2)]
        self.switches = [Switch(i, board_num) for i in range(4)]


class InputFunctionMap(list):
    """Maps inputs pins to callback functions.
    The callback function is passed a the input port as a byte

    map parameters (*optional):
    index    - input pin number
    into     - direction of change (into 1 or 0, 0 is pressed, None =either)
    callback - function to run when interupt is detected
    board*   - what PiFace digital board to check

    def callback(interupted_bit, input_byte):
         # input_byte = 0b11110111 <- pin 3 caused the interupt
         # input_byte = 0b10110111 <- pins 6 and 3 activated
        print(bin(input_byte))
    """
    def register(self, input_index, into, callback, board_index=0):
        self.append({
            'index': input_index,
            'into': into,
            'callback': callback,
            'board': board_index})


def init(init_board=True):
    """Initialises the PiFace Digital board"""
    pfcom.init(SPI_BUS, SPI_CHIP_SELECT)

    if init_board:
         # set up each board
        ioconfig = pfcom.BANK_OFF | \
            pfcom.INT_MIRROR_OFF | pfcom.SEQOP_ON | pfcom.DISSLW_OFF | \
            pfcom.HAEN_ON | pfcom.ODR_OFF | pfcom.INTPOL_LOW

        pfd_detected = False

        for board_index in range(MAX_BOARDS):
            pfcom.write(ioconfig, pfcom.IOCON, board_index)  # configure

            if not pfd_detected:
                if pfcom.read(pfcom.IOCON, board_index) == ioconfig:
                    pfd_detected = True

            pfcom.write(0, pfcom.GPIOA, board_index)  # clear port A
            pfcom.write(0, pfcom.IODIRA, board_index)  # set port A as outputs
            pfcom.write(0xff, pfcom.IODIRB, board_index)  # set port B as inputs
            pfcom.write(0xff, pfcom.GPPUB, board_index)  # set port B pullups on

        if not pfd_detected:
            raise NoPiFaceDigitalDetectedError(
                "There was no PiFace Digital board detected!"
            )


def deinit():
    """Closes the spidev file descriptor"""
    pfcom.deinit()


def digital_read(pin_num, board_num=0):
    """Returns the status of the input pin specified.
    1 is active
    0 is inactive
    Note: This function is for familiarality with Arduino users
    """
    return pfcom.read_bit(pin_num, INPUT_PORT, board_num) ^ 1


def digital_write(pin_num, value, board_num=0):
    """Writes the value specified to the output pin
    1 is active
    0 is inactive
    Note: This function is for familiarality with Arduino users
    """
    pfcom.write_bit(value, pin_num, OUTPUT_PORT, board_num)


def digital_read_pullup(pin_num, board_num=0):
    return pfcom.read_bit(pin_num, INPUT_PULLUP, board_num)


def digital_write_pullup(pin_num, value, board_num=0):
    pfcom.write_bit(value, pin_num, INPUT_PULLUP, board_num)


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
            disable_interupts()  # more graceful
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
        int_bit = pfcom.read(pfcom.INTFB, board_i)
        if int_bit == 0:
            continue  # The interupt has not been flagged on this board
        int_bit_num = pfcom.get_bit_num(int_bit)
        int_byte = pfcom.read(pfcom.INTCAPB, board_i)
        into = (int_bit & int_byte) >> int_bit_num  # bit changed into (0/1)

         # for each mapping (on this board) see if we have a callback
        for mapping in this_board_ifm:
            if int_bit_num == mapping['index'] and \
                    (mapping['into'] is None or into == mapping['into']):
                mapping['callback'](int_bit, int_byte)
                return  # one at a time


def clear_interupts():
    """Clears the interupt flags by pfcom.reading the capture register on all boards"""
    for i in range(MAX_BOARDS):
        pfcom.read(pfcom.INTCAPB, i)


def enable_interupts():
    for board_index in range(MAX_BOARDS):
        pfcom.write(0xff, pfcom.GPINTENB, board_index)

    # access quick2wire-gpio-admin for gpio pin twiddling
    try:
        subprocess.check_call(["gpio-admin", "export", "25"])
    except subprocess.CalledProcessError as e:
        if e.returncode != 4:  # we can ignore 4 (gpio25 is already up)
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
        if e.returncode != 4:  # we can ignore 4 (gpio25 is already down)
            raise e

    for board_index in range(MAX_BOARDS):
        pfcom.write(0, pfcom.GPINTENB, board_index)  # disable the interupt
