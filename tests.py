#!/usr/bin/env python3
from __future__ import print_function
import sys
import unittest
import threading
import pifacecommon
import pifacedigitalio
import argparse


PY3 = sys.version_info.major >= 3
if not PY3:
    input = raw_input

    from time import sleep

    class Barrier(object):
        def __init__(self, n, timeout=None):
            self.count = 0
            self.n = n
            self.timeout = timeout

        def wait(self):
            self.count += 1
            while self.count < self.n:
                sleep(0.0001)

    threading.Barrier = Barrier


OUTPUT_RANGE = LED_RANGE = INPUT_RANGE = 8
SWITCH_RANGE = 4
RELAY_RANGE = 2


class TestRangedItem(object):
    def test_normal_init(self):
        for i in self.item_range:
            item_instance = self.item_type(i)
            self.assertTrue(type(item_instance) is self.item_type)

    def test_boundary_init(self):
        boundaries = (min(self.item_range) - 1, max(self.item_range) + 1)
        for i in boundaries:
            self.assertRaises(
                pifacecommon.core.RangeError,
                self.item_type,
                i
            )


class TestLED(TestRangedItem, unittest.TestCase):
    def setUp(self):
        self.item_type = pifacedigitalio.LED
        self.item_range = range(LED_RANGE)


class TestSwitch(TestRangedItem, unittest.TestCase):
    def setUp(self):
        self.item_type = pifacedigitalio.Switch
        self.item_range = range(SWITCH_RANGE)


class TestRelay(TestRangedItem, unittest.TestCase):
    def setUp(self):
        self.item_type = pifacedigitalio.Relay
        self.item_range = range(RELAY_RANGE)


class TestDigitalRead(unittest.TestCase):
    def setUp(self):
        self.old_read_bit = pifacecommon.core.read_bit
        pifacedigitalio.init()
        # function is supposed to return 1, testing with 0
        pifacecommon.core.read_bit = lambda pin, port, board: 0

    def test_flip_bit(self):
        # digital_read should flip 0 to 1
        self.assertEqual(pifacedigitalio.digital_read(0, 0), 1)

    def tearDown(self):
        pifacedigitalio.deinit()
        pifacecommon.core.read_bit = self.old_read_bit


class TestPiFaceDigitalOutput(unittest.TestCase):
    def setUp(self):
        pifacedigitalio.init()

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

    def tearDown(self):
        pifacedigitalio.deinit()


class TestPiFaceDigitalInput(unittest.TestCase):
    """General use tests (not really in the spirit of unittesting)."""
    def setUp(self):
        pifacedigitalio.init()

    def test_switches(self):
        global pifacedigitals
        for pfd in pifacedigitals:
            for a, b in ((0, 2), (1, 3)):
                input(
                    "Hold switch {a} and {b} on board {board} and then "
                    "press enter.".format(a=a, b=b, board=pfd.hardware_addr))
                self.assertEqual(pfd.switches[a].value, 1)
                self.assertEqual(pfd.switches[a].value, 1)

                # while we're here, test the input pins
                self.assertEqual(pfd.input_pins[a].value, 1)
                self.assertEqual(pfd.input_pins[a].value, 1)

                # and the input port
                bit_pattern = (1 << a) ^ (1 << b)
                self.assertEqual(pfd.input_port.value, bit_pattern)

    # def test_input_pins(self):
    #     if TEST_INPUT_PORT:
    #         for i in range(INPUT_RANGE):
    #             input("Connect input {i}, then press enter.".format(i=i))
    #             self.assertEqual(self.pfd.switches[i].value, 1)

    # def test_input_port(self):
    #     if TEST_INPUT_PORT:
    #         input("Connect pins 0, 2, 4 and 6, then press enter.")
    #         self.assertEqual(self.pfd.input_port.value, 0xAA)
    #         input("Connect pins 1, 3, 5 and 7, then press enter.")
    #         self.assertEqual(self.pfd.input_port.value, 0x55)

    def tearDown(self):
        pifacedigitalio.deinit()


class TestInterrupts(unittest.TestCase):
    def setUp(self):
        pifacedigitalio.init()
        self.direction = pifacedigitalio.IODIR_ON
        self.barriers = dict()
        self.board_switch_pressed = list()
        self.listeners = list()

        global pifacedigitals
        for p in pifacedigitals:
            self.barriers[p.hardware_addr] = threading.Barrier(2, timeout=10)
            listener = pifacedigitalio.InputEventListener(p.hardware_addr)
            listener.register(0, self.direction, self.interrupts_test_helper)
            self.listeners.append(listener)

    def test_interrupt(self):
        for listener in self.listeners:
            listener.activate()
        print("Press switch 0 on every board.")
        barriers = self.barriers.items() if PY3 else self.barriers.iteritems()
        for hardware_addr, barrier in barriers:
            barrier.wait()
        global pifacedigitals
        for p in pifacedigitals:
            self.assertTrue(p.hardware_addr in self.board_switch_pressed)

    def interrupts_test_helper(self, event):
        self.assertEqual(event.interrupt_flag, 0x1)
        self.assertEqual(event.interrupt_capture, 0xfe)
        self.assertEqual(event.pin_num, 0)
        self.assertEqual(event.direction, self.direction)
        self.board_switch_pressed.append(event.hardware_addr)
        print("Switch 0 on board {} pressed.".format(event.hardware_addr))
        self.barriers[event.hardware_addr].wait()

    def tearDown(self):
        for listener in self.listeners:
            listener.deactivate()
        pifacedigitalio.deinit()


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

    boards_string = ", ".join([str(pfd.hardware_addr) for pfd in pifacedigitals])
    print("Testing boards:", boards_string)

    unittest.main()
