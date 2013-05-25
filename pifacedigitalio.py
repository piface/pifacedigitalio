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
import time
import pifacecommon as pfcom

# /dev/spidev<bus>.<chipselect>
SPI_BUS = 0
SPI_CHIP_SELECT = 0

# some easier to remember/read values
OUTPUT_PORT = pfcom.GPIOA
INPUT_PORT = pfcom.GPIOB
INPUT_PULLUP = pfcom.GPPUB
IN_EVENT_DIR_ON = 0
IN_EVENT_DIR_OFF = 1
IN_EVENT_DIR_BOTH = None

GPIO_INTERRUPT_PIN = 25
GPIO_INTERRUPT_DEVICE = "/sys/devices/virtual/gpio/gpio%d" % GPIO_INTERRUPT_PIN
GPIO_INTERRUPT_DEVICE_EDGE = '%s/edge' % GPIO_INTERRUPT_DEVICE
GPIO_INTERRUPT_DEVICE_VALUE = '%s/value' % GPIO_INTERRUPT_DEVICE
GPIO_EXPORT_FILE = "/sys/class/gpio/export"
GPIO_UNEXPORT_FILE = "/sys/class/gpio/unexport"

# max seconds to wait for file I/O (when enabling interrupts)
FILE_IO_TIMEOUT = 1


class InitError(Exception):
    pass


class NoPiFaceDigitalDetectedError(Exception):
    pass


class Timeout(Exception):
    pass


class InterruptEnableException(Exception):
    pass


class LED(pfcom.DigitalOutputItem):
    """An LED on PiFace Digital"""
    def __init__(self, led_num, board_num=0):
        if led_num < 0 or led_num > 7:
            raise pfcom.RangeError(
                "Specified LED index (%d) out of range." % led_num)
        else:
            super().__init__(led_num, OUTPUT_PORT, board_num)


class Relay(pfcom.DigitalOutputItem):
    """A relay on PiFace Digital"""
    def __init__(self, relay_num, board_num=0):
        if relay_num < 0 or relay_num > 1:
            raise pfcom.RangeError(
                "Specified relay index (%d) out of range." % relay_num)
        else:
            super().__init__(relay_num, OUTPUT_PORT, board_num)


class Switch(pfcom.DigitalInputItem):
    """A switch on PiFace Digital"""
    def __init__(self, switch_num, board_num=0):
        if switch_num < 0 or switch_num > 3:
            raise pfcom.RangeError(
                "Specified switch index (%d) out of range." % switch_num)
        else:
            super().__init__(switch_num, INPUT_PORT, board_num)


class PiFaceDigital(object):
    """A single PiFace Digital board"""
    def __init__(self, board_num=0):
        self.board_num = board_num
        self.input_pins = [pfcom.DigitalInputItem(i, INPUT_PORT, board_num) \
                for i in range(8)]
        self.output_pins = [pfcom.DigitalOutputItem(i, OUTPUT_PORT, board_num) \
                for i in range(8)]
        self.leds = [LED(i, board_num) for i in range(8)]
        self.relays = [Relay(i, board_num) for i in range(2)]
        self.switches = [Switch(i, board_num) for i in range(4)]


class InputFunctionMap(list):
    """Maps inputs pins to functions.

    Use the register method to map inputs to functions.

    Each function is passed the interrupt bit map as a byte and the input
    port as a byte. The return value of the function specifies whether the
    wait_for_input loop should continue (True is continue).

    Register Parameters (*optional):
    input_index - input pin number
    direction   - direction of change
                        IN_EVENT_DIR_ON
                        IN_EVENT_DIR_OFF
                        IN_EVENT_DIR_BOTH
    callback    - function to run when interrupt is detected
    board*      - what PiFace digital board to check

    Example:
    def my_callback(interrupted_bit, input_byte):
         # if interrupted_bit = 0b00001000: pin 3 caused the interrupt
         # if input_byte = 0b10110111: pins 6 and 3 activated
        print(bin(interrupted_bit), bin(input_byte))
        return True  # keep waiting for interrupts
    """
    def register(self, input_index, direction, callback, board_index=0):
        self.append({
            'index': input_index,
            'direction': direction,
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

        for board_index in range(pfcom.MAX_BOARDS):
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


# interrupts
def wait_for_input(input_func_map=None, timeout=None):
    """Waits for an input port event (change)

    Paramaters:
    input_func_map - An InputFunctionMap object describing callbacks
    timeout        - How long we should wait before giving up and exiting the
                     function
    """
    enable_interrupts()

    # set up epoll (can't do it in enable_interrupts for some reason)
    gpio25 = open(GPIO_INTERRUPT_DEVICE_VALUE, 'r')
    epoll = select.epoll()
    epoll.register(gpio25, select.EPOLLIN | select.EPOLLET)

    # always ignore the first event (I'm not sure why; this is a bad)
    #_wait_for_event(epoll, timeout)

    while True:
        # wait here until input
        try:
            events = _wait_for_event(epoll, timeout)
        except KeyboardInterrupt:
            break

        # if we have some events...
        if len(events) <= 0:
            break

        # ...and a map
        if input_func_map:
            keep_waiting = _call_mapped_input_functions(input_func_map)
            if not keep_waiting:
                break
        else:
            break  # there is no ifm

    epoll.close()
    disable_interrupts()


def _wait_for_event(epoll, timeout=None):
    """Waits for an event on the epoll, returns a list of events
    This will hang, may throw KeyboardInterrupt
    """
    return epoll.poll(timeout) if timeout else epoll.poll()


def _call_mapped_input_functions(input_func_map):
    """Finds which board caused the interrupt and calls the mapped
    function.
    Returns whether the wait_for_input function should keep waiting for input
    """
    for board_i in range(MAX_BOARDS):
        this_board_ifm = [m for m in input_func_map if m['board'] == board_i]

        # read the interrupt status of this PiFace board
        # interrupt bit (int_bit) - bit map showing what caused the interrupt
        int_bit = pfcom.read(pfcom.INTFB, board_i)
        if int_bit == 0:
            continue  # The interrupt has not been flagged on this board
        int_bit_num = pfcom.get_bit_num(int_bit)
        
        # interrupt byte (int_byte) - snapshot of in port when int occured
        int_byte = pfcom.read(pfcom.INTCAPB, board_i)

        # direction - whether the bit changed into a 1 or a 0
        direction = (int_bit & int_byte) >> int_bit_num

        # for each mapping (on this board) see if we have a callback
        for mapping in this_board_ifm:
            if int_bit_num == mapping['index'] and \
                    (mapping['direction'] is None or
                        direction == mapping['direction']):
                # run the callback
                keep_waiting = mapping['callback'](int_bit, int_byte)

                # stop waiting for interrupts, by default
                if keep_waiting is None:
                    keep_waiting = False

                return keep_waiting

    # This event does not have a mapped function, keep waiting
    return True


def clear_interrupts():
    """Clears the interrupt flags by 'pfcom.read'ing the capture register
    on all boards
    """
    for i in range(MAX_BOARDS):
        pfcom.read(pfcom.INTCAPB, i)


def enable_interrupts():
    # enable interrupts
    for board_index in range(MAX_BOARDS):
        pfcom.write(0xff, pfcom.GPINTENB, board_index)

    try:
        _bring_gpio_interrupt_into_userspace()
        _set_gpio_interrupt_edge()
    except Timeout as e:
        raise InterruptEnableException(
            "There was an error bringing gpio%d into userspace. %s" % \
            (GPIO_INTERRUPT_PIN, e.message)
        )


def _bring_gpio_interrupt_into_userspace():
    try:
        # is it already there?
        with open(GPIO_INTERRUPT_DEVICE_VALUE): return
    except IOError:
        # no, bring it into userspace
        with open(GPIO_EXPORT_FILE, 'w') as export_file:
            export_file.write(str(GPIO_INTERRUPT_PIN))

        _wait_until_file_exists(GPIO_INTERRUPT_DEVICE_VALUE)


def _set_gpio_interrupt_edge():
    # we're only interested in the falling edge (1 -> 0)
    start_time = time.time()
    time_limit = start_time + FILE_IO_TIMEOUT
    while time.time() < time_limit:
        try:
            with open(GPIO_INTERRUPT_DEVICE_EDGE, 'w') as gpio_edge:
                gpio_edge.write('falling')
                return
        except IOError:
            pass


def _wait_until_file_exists(filename):
    start_time = time.time()
    time_limit = start_time + FILE_IO_TIMEOUT
    while time.time() < time_limit:
        try:
            with open(filename): return
        except IOError:
            pass
    
    raise Timeout("Waiting too long for %s." % filename)


def disable_interrupts():
    # neither edge
    with open(GPIO_INTERRUPT_DEVICE_EDGE, 'w') as gpio25edge:
        gpio25edge.write('none')

    # remove the pin from userspace
    with open(GPIO_UNEXPORT_FILE, 'w') as unexport_file:
        unexport_file.write(str(GPIO_INTERRUPT_PIN))

    # disable the interrupt
    for board_index in range(MAX_BOARDS):
        pfcom.write(0, pfcom.GPINTENB, board_index)
