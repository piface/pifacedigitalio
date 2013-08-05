# -*- coding: utf-8 -*-
import select
import subprocess
import time
import pifacecommon

# /dev/spidev<bus>.<chipselect>
SPI_BUS = 0
SPI_CHIP_SELECT = 0

# some easier to remember/read values
OUTPUT_PORT = pifacecommon.core.GPIOA
INPUT_PORT = pifacecommon.core.GPIOB
INPUT_PULLUP = pifacecommon.core.GPPUB


class InitError(Exception):
    pass


class NoPiFaceDigitalDetectedError(Exception):
    pass


class LED(pifacecommon.core.DigitalOutputItem):
    """An LED on a PiFace Digital board. Inherits
    :class:`pifacecommon.core.DigitalOutputItem`.
    """
    def __init__(self, led_num, board_num=0):
        if led_num < 0 or led_num > 7:
            raise pifacecommon.core.RangeError(
                "Specified LED index (%d) out of range." % led_num)
        else:
            super(LED, self).__init__(led_num, OUTPUT_PORT, board_num)


class Relay(pifacecommon.core.DigitalOutputItem):
    """A relay on a PiFace Digital board. Inherits
    :class:`pifacecommon.core.DigitalOutputItem`.
    """
    def __init__(self, relay_num, board_num=0):
        if relay_num < 0 or relay_num > 1:
            raise pifacecommon.core.RangeError(
                "Specified relay index (%d) out of range." % relay_num)
        else:
            super(Relay, self).__init__(relay_num, OUTPUT_PORT, board_num)


class Switch(pifacecommon.core.DigitalInputItem):
    """A switch on a PiFace Digital board. Inherits
    :class:`pifacecommon.core.DigitalInputItem`.
    """
    def __init__(self, switch_num, board_num=0):
        if switch_num < 0 or switch_num > 3:
            raise pifacecommon.core.RangeError(
                "Specified switch index (%d) out of range." % switch_num)
        else:
            super(Switch, self).__init__(switch_num, INPUT_PORT, board_num)


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
        self.input_port = \
            pifacecommon.core.DigitalInputPort(INPUT_PORT, board_num)
        self.output_port = \
            pifacecommon.core.DigitalOutputPort(OUTPUT_PORT, board_num)
        self.input_pins = [
            pifacecommon.core.DigitalInputItem(i, INPUT_PORT, board_num)
            for i in range(8)
        ]
        self.output_pins = [
            pifacecommon.core.DigitalOutputItem(
                i, OUTPUT_PORT, board_num) for i in range(8)
        ]
        self.leds = [LED(i, board_num) for i in range(8)]
        self.relays = [Relay(i, board_num) for i in range(2)]
        self.switches = [Switch(i, board_num) for i in range(4)]


class InputEventListener(pifacecommon.interrupts.PortEventListener):
    """Listens for events on the input port and calls the mapped callback
    functions.

    >>> def print_flag(event):
    ...     print(event.interrupt_flag)
    ...
    >>> listener = pifacedigitalio.InputEventListener()
    >>> listener.register(0, pifacedigitalio.IODIR_ON, print_flag)
    >>> listener.activate()
    """
    def __init__(self, board_num=0):
        super(InputEventListener, self).__init__(INPUT_PORT, board_num)


def init(init_board=True):
    """Initialises all PiFace Digital boards.

    :param init_board: Initialise each board (default: True)
    :type init_board: boolean
    :raises: :class:`NoPiFaceDigitalDetectedError`
    """
    pifacecommon.core.init(SPI_BUS, SPI_CHIP_SELECT)

    if init_board:
         # set up each board
        ioconfig = (
            pifacecommon.core.BANK_OFF |
            pifacecommon.core.INT_MIRROR_OFF |
            pifacecommon.core.SEQOP_OFF |
            pifacecommon.core.DISSLW_OFF |
            pifacecommon.core.HAEN_ON |
            pifacecommon.core.ODR_OFF |
            pifacecommon.core.INTPOL_LOW
        )

        pfd_detected = False

        for board_index in range(pifacecommon.core.MAX_BOARDS):
            pifacecommon.core.write(
                ioconfig, pifacecommon.core.IOCON, board_index)

            if not pfd_detected:
                pfioconf = pifacecommon.core.read(
                    pifacecommon.core.IOCON, board_index)
                if pfioconf == ioconfig:
                    pfd_detected = True

            # clear port A and set it as an output
            pifacecommon.core.write(0, pifacecommon.core.GPIOA, board_index)
            pifacecommon.core.write(0, pifacecommon.core.IODIRA, board_index)
            # set port B as input and turn pullups on
            pifacecommon.core.write(
                0xff, pifacecommon.core.IODIRB, board_index)
            pifacecommon.core.write(0xff, pifacecommon.core.GPPUB, board_index)

        if not pfd_detected:
            raise NoPiFaceDigitalDetectedError(
                "No PiFace Digital board detected!"
            )
        else:
            pifacecommon.interrupts.enable_interrupts(INPUT_PORT)


def deinit():
    """Closes the spidev file descriptor"""
    pifacecommon.interrupts.disable_interrupts(INPUT_PORT)
    pifacecommon.core.deinit()


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
    return pifacecommon.core.read_bit(pin_num, INPUT_PORT, board_num) ^ 1


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
    pifacecommon.core.write_bit(value, pin_num, OUTPUT_PORT, board_num)


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
    return pifacecommon.core.read_bit(pin_num, INPUT_PULLUP, board_num)


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
    pifacecommon.core.write_bit(value, pin_num, INPUT_PULLUP, board_num)
