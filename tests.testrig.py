#!/usr/bin/env python3
from __future__ import print_function
import sys
import unittest
import threading
import pifacecommon
import pifacedigitalio
import argparse
import time
import multiprocessing


PY3 = sys.version_info.major >= 3
if not PY3:
    input = raw_input

    class Barrier(object):
        def __init__(self, n, timeout=None):
            self.count = 0
            self.n = n
            self.timeout = timeout

        def wait(self):
            self.count += 1
            while self.count < self.n:
                time.sleep(0.0001)

    threading.Barrier = Barrier


OUTPUT_RANGE = LED_RANGE = INPUT_RANGE = 8
SWITCH_RANGE = 4
RELAY_RANGE = 2


class TestPiFaceDigitalOutput(unittest.TestCase):
    def setUp(self):
        pifacedigitalio.init()  # for digital write

    def test_leds(self):
        global pifacedigitals
        for pfd in pifacedigitals:
            for i in range(LED_RANGE):
                pfd.leds[i].turn_on()
                self.assertEqual(pfd.output_pins[i].value, 1)
                pfd.leds[i].toggle()
                self.assertEqual(pfd.output_pins[i].value, 0)
                pfd.leds[i].toggle()
                self.assertEqual(pfd.output_pins[i].value, 1)
                pfd.leds[i].turn_off()
                self.assertEqual(pfd.output_pins[i].value, 0)

    def test_relays(self):
        global pifacedigitals
        for pfd in pifacedigitals:
            for i in range(RELAY_RANGE):
                pfd.relays[i].turn_on()
                self.assertEqual(pfd.relays[i].value, 1)
                pfd.relays[i].toggle()
                self.assertEqual(pfd.relays[i].value, 0)
                pfd.relays[i].toggle()
                self.assertEqual(pfd.relays[i].value, 1)
                pfd.relays[i].turn_off()
                self.assertEqual(pfd.relays[i].value, 0)

    def test_output_pins(self):
        global pifacedigitals
        for pfd in pifacedigitals:
            for i in range(OUTPUT_RANGE):
                pfd.output_pins[i].turn_on()
                self.assertEqual(pfd.output_pins[i].value, 1)
                pfd.output_pins[i].toggle()
                self.assertEqual(pfd.output_pins[i].value, 0)
                pfd.output_pins[i].toggle()
                self.assertEqual(pfd.output_pins[i].value, 1)
                pfd.output_pins[i].turn_off()
                self.assertEqual(pfd.output_pins[i].value, 0)

    def test_output_port(self):
        global pifacedigitals
        for pfd in pifacedigitals:
            test_value = 0xAA
            pfd.output_port.all_on()
            self.assertEqual(pfd.output_port.value, 0xFF)
            pfd.output_port.value = test_value
            self.assertEqual(pfd.output_port.value, test_value)
            pfd.output_port.toggle()
            self.assertEqual(pfd.output_port.value, 0xff ^ test_value)
            pfd.output_port.toggle()
            self.assertEqual(pfd.output_port.value, test_value)
            pfd.output_port.all_off()
            self.assertEqual(pfd.output_port.value, 0)

    def test_digital_write(self):
        global pifacedigitals
        for pfd in pifacedigitals:
            for pin in range(8):
                pifacedigitalio.digital_write(pin, 1, pfd.hardware_addr)
                self.assertEqual(pfd.output_port.bits[pin].value, 1)
                pifacedigitalio.digital_write(pin, 0, pfd.hardware_addr)
                self.assertEqual(pfd.output_port.bits[pin].value, 0)

    def tearDown(self):
        pifacedigitalio.deinit()  # for digital write


class TestPiFaceDigitalInput(unittest.TestCase):
    """Outputs are connected to inputs but reversed:
        input 0 - output 7
        input 1 - output 6
        input 2 - output 5
        input 3 - output 4
        input 4 - output 3
        input 5 - output 2
        input 6 - output 1
        input 7 - output 0
    """
    def setUp(self):
        pifacedigitalio.init()  # for digital read

    def test_switches(self):
        global pifacedigitals
        for pfd in pifacedigitals:
            for a, b in ((0, 2), (1, 3)):
                # user input
                # input(
                #     "Hold switch {a} and {b} on board {board} and then "
                #     "press enter.".format(a=a, b=b, board=pfd.hardware_addr))
                # test rig input
                pfd.output_pins[7-a].turn_on()
                pfd.output_pins[7-b].turn_on()

                self.assertEqual(pfd.switches[a].value, 1)
                self.assertEqual(pfd.switches[b].value, 1)

                # while we're here, test the input pins
                self.assertEqual(pfd.input_pins[a].value, 1)
                self.assertEqual(
                    pifacedigitalio.digital_read(a, pfd.hardware_addr),
                    1)
                self.assertEqual(pfd.input_pins[b].value, 1)

                # and the input port
                bit_pattern = (1 << a) ^ (1 << b)
                self.assertEqual(pfd.input_port.value, bit_pattern)

                # test rig input
                pfd.output_pins[7-a].turn_off()
                pfd.output_pins[7-b].turn_off()

    def test_input_pins(self):
        for pfd in pifacedigitals:
            for i in range(INPUT_RANGE):
                # input("Connect input {i}, then press enter.".format(i=i))
                pfd.output_pins[7-i].turn_on()
                self.assertEqual(pfd.input_pins[i].value, 1)
                pfd.output_pins[7-i].turn_off()

    def test_input_port(self):
        for pfd in pifacedigitals:
            # input("Connect pins 0, 2, 4 and 6, then press enter.")
            pfd.output_port.value = 0x55
            self.assertEqual(pfd.input_port.value, 0xAA)
            # input("Connect pins 1, 3, 5 and 7, then press enter.")
            pfd.output_port.value = 0xAA
            self.assertEqual(pfd.input_port.value, 0x55)
            pfd.output_port.value = 0

    def tearDown(self):
        pifacedigitalio.deinit()  # for digital read


class TestInterrupts(unittest.TestCase):
    def setUp(self):
        # pifacedigitalio.init()
        self.direction = pifacedigitalio.IODIR_ON
        self.barriers = dict()
        self.board_switch_pressed = list()
        self.listeners = list()

        global pifacedigitals
        for p in pifacedigitals:
            self.barriers[p.hardware_addr] = threading.Barrier(2, timeout=10)
            listener = pifacedigitalio.InputEventListener(p)
            listener.register(0, self.direction, self.interrupts_test_helper)
            self.listeners.append(listener)

    def test_interrupt(self):
        for listener in self.listeners:
            listener.activate()
        # print("Press switch 0 on every board.")
        barriers = self.barriers.items() if PY3 else self.barriers.iteritems()
        for hardware_addr, barrier in barriers:
            p = multiprocessing.Process(target=simulate_button_press,
                                        args=(7, hardware_addr, 0.5))
            p.start()
        # for hardware_addr, barrier in barriers:
            barrier.wait()

        global pifacedigitals
        for p in pifacedigitals:
            self.assertTrue(p.hardware_addr in self.board_switch_pressed)

    def interrupts_test_helper(self, event):
        self.assertEqual(event.interrupt_flag, 0x1)
        self.assertEqual(event.interrupt_capture, 0xfe)
        self.assertEqual(event.pin_num, 0)
        self.assertEqual(event.direction, self.direction)
        self.board_switch_pressed.append(event.chip.hardware_addr)
        # print("Switch 0 on board {} pressed.".format(event.hardware_addr))
        self.barriers[event.chip.hardware_addr].wait()

    def tearDown(self):
        for listener in self.listeners:
            listener.deactivate()
        # pifacedigitalio.deinit()


def simulate_button_press(pin_num=0, hardware_addr=0, hold_time=0.5):
    """Simulate a button press and unpress."""
    pfd = pifacedigitalio.PiFaceDigital(hardware_addr)
    pfd.output_pins[pin_num].turn_on()
    time.sleep(hold_time)
    pfd.output_pins[pin_num].turn_off()


class TestBigDigitalReadWrite(unittest.TestCase):
    def setUp(self):
        pifacedigitalio.init()

    def test_big_digital_read_write(self):
        pin = 0
        for i in range(1000):
            for test_value in (1, 0):
                pifacedigitalio.digital_write(pin, test_value)
                v = pifacedigitalio.digital_read(7 - pin)
                self.assertEqual(test_value, v)


def remove_arg(shortarg, longarg):
    try:
        sys.argv.remove(longarg)
    except ValueError:
        sys.argv.remove(shortarg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b0", "--board0", help="test PiFace Digital board 0 (default)",
        action="store_true")
    for i in range(1, 4):
        parser.add_argument(
            "-b{}".format(i),
            "--board{}".format(i),
            help="test PiFace Digital board {}".format(i),
            action="store_true")
    args = parser.parse_args()

    global pifacedigitals
    pifacedigitals = list()

    if args.board0 or not (args.board1 or args.board2 or args.board3):
        pifacedigitals.append(pifacedigitalio.PiFaceDigital(0))
        if args.board0:
            remove_arg("-b0", "--board0")

    if args.board1:
        pifacedigitals.append(pifacedigitalio.PiFaceDigital(1))
        remove_arg("-b1", "--board1")

    if args.board2:
        pifacedigitals.append(pifacedigitalio.PiFaceDigital(2))
        remove_arg("-b2", "--board2")

    if args.board3:
        pifacedigitals.append(pifacedigitalio.PiFaceDigital(3))
        remove_arg("-b3", "--board3")

    hardware_addrs = \
        ", ".join([str(pfd.hardware_addr) for pfd in pifacedigitals])
    print("Testing PiFace Digital's with address:", hardware_addrs)

    unittest.main()
