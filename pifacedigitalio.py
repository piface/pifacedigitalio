#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import time
import pifacecommon as pfcom


# /dev/spidev<bus>.<chipselect>
SPI_BUS = 0
SPI_CHIP_SELECT = 0

# some easier to remember/read values
OUTPUT_PORT = pfcom.GPIOA
INPUT_PORT = pfcom.GPIOB
INPUT_PULLUP = pfcom.GPPUB


class InitError(Exception):
    pass


class NoPiFaceDigitalDetectedError(Exception):
    pass


class LED(pfcom.DigitalOutputItem):
    """An LED on a PiFace Digital board. Inherits
    :class:`pifacecommon.core.DigitalOutputItem`.
    """
    def __init__(self, led_num, board_num=0):
        if led_num < 0 or led_num > 7:
            raise pfcom.core.RangeError(
                "Specified LED index (%d) out of range." % led_num)
        else:
            super().__init__(led_num, OUTPUT_PORT, board_num)


class Relay(pfcom.DigitalOutputItem):
    """A relay on a PiFace Digital board. Inherits
    :class:`pifacecommon.core.DigitalOutputItem`.
    """
    def __init__(self, relay_num, board_num=0):
        if relay_num < 0 or relay_num > 1:
            raise pfcom.core.RangeError(
                "Specified relay index (%d) out of range." % relay_num)
        else:
            super().__init__(relay_num, OUTPUT_PORT, board_num)


class Switch(pfcom.DigitalInputItem):
    """A switch on a PiFace Digital board. Inherits
    :class:`pifacecommon.core.DigitalInputItem`.
    """
    def __init__(self, switch_num, board_num=0):
        if switch_num < 0 or switch_num > 3:
            raise pfcom.core.RangeError(
                "Specified switch index (%d) out of range." % switch_num)
        else:
            super().__init__(switch_num, INPUT_PORT, board_num)


class PiFaceDigital(object):
    """A PiFace Digital board.

    :attribute: board_num -- The board number.
    :attribute: input_port -- See :class:`pifacecommon.core.DigitalInputPort`.
    :attribute: output_port -- See
        :class:`pifacecommon.core.DigitalOutputPort`.
    :attribute: input_pins -- list containing
        :class:`pifacecommon.core.DigitalInputPin`.
    :attribute: output_pins -- list containing
        :class:`pifacecommon.core.DigitalOutputPin`.
    :attribute: leds -- list containing :class:`LED`.
    :attribute: relays -- list containing :class:`Relay`.
    :attribute: switches -- list containing :class:`Switch`.

    Example:

    >>> pfd = pifacedigitalio.PiFaceDigital()
    >>> pfd.input_port.value
    0
    >>> pfd.output_port.value = 0xAA
    >>> pfd.leds[5].turn_on()
    """
    def __init__(self, board_num=0):
        self.board_num = board_num
        self.input_port = pfcom.DigitalInputPort(INPUT_PORT, board_num)
        self.output_port = pfcom.DigitalOutputPort(OUTPUT_PORT, board_num)
        self.input_pins = [
            pfcom.DigitalInputItem(i, INPUT_PORT, board_num) for i in range(8)
        ]
        self.output_pins = [
            pfcom.DigitalOutputItem(
                i, OUTPUT_PORT, board_num) for i in range(8)
        ]
        self.leds = [LED(i, board_num) for i in range(8)]
        self.relays = [Relay(i, board_num) for i in range(2)]
        self.switches = [Switch(i, board_num) for i in range(4)]


def init(init_board=True):
    """Initialises all PiFace Digital boards.

    :param init_board: Initialise each board (default: True)
    :type init_board: boolean
    :raises: :class:`NoPiFaceDigitalDetectedError`
    """
    pfcom.init(SPI_BUS, SPI_CHIP_SELECT)

    if init_board:
         # set up each board
        ioconfig = pfcom.BANK_OFF | \
            pfcom.INT_MIRROR_OFF | pfcom.SEQOP_OFF | pfcom.DISSLW_OFF | \
            pfcom.HAEN_ON | pfcom.ODR_OFF | pfcom.INTPOL_LOW

        pfd_detected = False

        for board_index in range(pfcom.MAX_BOARDS):
            pfcom.write(ioconfig, pfcom.IOCON, board_index)  # configure

            if not pfd_detected:
                if pfcom.read(pfcom.IOCON, board_index) == ioconfig:
                    pfd_detected = True

            pfcom.write(0, pfcom.GPIOA, board_index)  # clear port A
            pfcom.write(0, pfcom.IODIRA, board_index)  # port A as outputs
            pfcom.write(0xff, pfcom.IODIRB, board_index)  # port B as inputs
            pfcom.write(0xff, pfcom.GPPUB, board_index)  # port B pullups on

        if not pfd_detected:
            raise NoPiFaceDigitalDetectedError(
                "There was no PiFace Digital board detected!"
            )


def deinit():
    """Closes the spidev file descriptor"""
    pfcom.deinit()


# wrapper functions for backwards compatibility
def digital_read(pin_num, board_num=0):
    """Returns the value of the input pin specified.

    .. note:: This function is for familiarality with users of other types of
       IO board. Consider using :func:`pifacecommon.core.read_bit` instead.

       >>> pifacecommon.core.read_bit(pin_num, INPUT_PORT, board_num)

    :param pin_num: The pin number to read.
    :type pin_num: int
    :param board_num: The board to read from (default: 0)
    :type board_num: int
    :returns: int -- value of the pin
    """
    return pfcom.read_bit(pin_num, INPUT_PORT, board_num) ^ 1


def digital_write(pin_num, value, board_num=0):
    """Writes the value to the input pin specified.

    .. note:: This function is for familiarality with users of other types of
       IO board. Consider using :func:`pifacecommon.core.write_bit` instead.

       >>> pifacecommon.core.write_bit(value, pin_num, OUTPUT_PORT, board_num)

    :param pin_num: The pin number to write to.
    :type pin_num: int
    :param value: The value to write.
    :type value: int
    :param board_num: The board to read from (default: 0)
    :type board_num: int
    """
    pfcom.write_bit(value, pin_num, OUTPUT_PORT, board_num)


def digital_read_pullup(pin_num, board_num=0):
    """Returns the value of the input pullup specified.

    .. note:: This function is for familiarality with users of other types of
       IO board. Consider using :func:`pifacecommon.core.read_bit` instead.

       >>> pifacecommon.core.read_bit(pin_num, INPUT_PULLUP, board_num)

    :param pin_num: The pin number to read.
    :type pin_num: int
    :param board_num: The board to read from (default: 0)
    :type board_num: int
    :returns: int -- value of the pin
    """
    return pfcom.read_bit(pin_num, INPUT_PULLUP, board_num)


def digital_write_pullup(pin_num, value, board_num=0):
    """Writes the value to the input pullup specified.

    .. note:: This function is for familiarality with users of other types of
       IO board. Consider using :func:`pifacecommon.core.write_bit` instead.

       >>> pifacecommon.core.write_bit(value, pin_num, INPUT_PULLUP, board_num)

    :param pin_num: The pin number to write to.
    :type pin_num: int
    :param value: The value to write.
    :type value: int
    :param board_num: The board to read from (default: 0)
    :type board_num: int
    """
    pfcom.write_bit(value, pin_num, INPUT_PULLUP, board_num)


# interrupts
def wait_for_input(input_func_map=None, timeout=None):
    """Waits for an port event (change) and runs the callback function tied to
    that.

    :param input_func_map: An InputFunctionMap object describing callbacks.
    :type input_func_map: :class:`pifacecommon.interrupts.InputFunctionMap`
    :param timeout: How long we should wait before giving up.
    :type timeout: int
    """
    pfcom.wait_for_interrupt(INPUT_PORT, input_func_map, timeout)
