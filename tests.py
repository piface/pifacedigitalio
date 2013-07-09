#!/usr/bin/env python3
import sys
import unittest
import threading
import pifacecommon
import pifacedigitalio


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

TEST_INPUT_PORT = False


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
        pifacedigitalio.init()
        # function is supposed to return 1
        pifacecommon.read_bit = lambda pin, port, board: 1

    def test_flip_bit(self):
        # should flip 1 to 0
        self.assertEqual(pifacedigitalio.digital_read(0, 0), 0)

    def tearDown(self):
        pifacedigitalio.deinit()


class TestPiFaceDigitalOutput(unittest.TestCase):
    """General use tests (not really in the spirit of unittesting)."""
    def setUp(self):
        pifacedigitalio.init()
        self.pfd = pifacedigitalio.PiFaceDigital()

    def test_leds(self):
        for i in range(LED_RANGE):
            self.pfd.leds[i].turn_on()
            self.pfd.leds[i].toggle()
            self.pfd.leds[i].toggle()
            self.pfd.leds[i].turn_off()

    def test_relays(self):
        for i in range(RELAY_RANGE):
            self.pfd.relays[i].turn_on()
            self.pfd.relays[i].toggle()
            self.pfd.relays[i].toggle()
            self.pfd.relays[i].turn_off()

    def test_output_pins(self):
        for i in range(OUTPUT_RANGE):
            self.pfd.output_pins[i].turn_on()
            self.pfd.output_pins[i].toggle()
            self.pfd.output_pins[i].toggle()
            self.pfd.output_pins[i].turn_off()

    def test_output_port(self):
        test_value = 0xAA

        self.pfd.output_port.all_on()
        self.assertEqual(self.pfd.output_port.value, 0xFF)

        self.pfd.output_port.value = test_value
        self.assertEqual(self.pfd.output_port.value, test_value)

        self.pfd.output_port.toggle()
        self.assertEqual(self.pfd.output_port.value, 0xff ^ test_value)

        self.pfd.output_port.toggle()
        self.assertEqual(self.pfd.output_port.value, test_value)

        self.pfd.output_port.all_off()
        self.assertEqual(self.pfd.output_port.value, 0)

    def tearDown(self):
        pifacedigitalio.deinit()


class TestPiFaceDigitalInput(unittest.TestCase):
    """General use tests (not really in the spirit of unittesting)."""
    def setUp(self):
        pifacedigitalio.init()
        self.pfd = pifacedigitalio.PiFaceDigital()

    def test_switches(self):
        for a, b in ((0, 2), (1, 3)):
            input(
                "Hold switch {a} and {b}, then press enter.".format(a=a, b=b))
            self.assertEqual(self.pfd.switches[a].value, 1)
            self.assertEqual(self.pfd.switches[a].value, 1)

            # while we're here, test the input pins
            self.assertEqual(self.pfd.input_pins[a].value, 1)
            self.assertEqual(self.pfd.input_pins[a].value, 1)

            # and the input port
            bit_pattern = (1 << a) ^ (1 << b)
            self.assertEqual(self.pfd.input_port.value, bit_pattern)

    def test_input_pins(self):
        if TEST_INPUT_PORT:
            for i in range(INPUT_RANGE):
                input("Connect input {i}, then press enter.".format(i=i))
                self.assertEqual(self.pfd.switches[i].value, 1)

    def test_input_port(self):
        if TEST_INPUT_PORT:
            input("Connect pins 0, 2, 4 and 6, then press enter.")
            self.assertEqual(self.pfd.input_port.value, 0xAA)
            input("Connect pins 1, 3, 5 and 7, then press enter.")
            self.assertEqual(self.pfd.input_port.value, 0x55)

    def tearDown(self):
        pifacedigitalio.deinit()


class TestInterrupts(unittest.TestCase):
    def setUp(self):
        pifacedigitalio.init()
        self.barrier = threading.Barrier(2, timeout=5)
        self.test_passed = False
        self.direction = pifacedigitalio.IODIR_ON
        self.listener = pifacedigitalio.InputEventListener()
        self.listener.register(0, self.direction, self.interrupts_test_helper)

    def test_interrupt(self):
        self.listener.activate()
        self.barrier.wait()
        self.assertTrue(self.test_passed)

    def interrupts_test_helper(self, event):
        self.assertEqual(event.interrupt_flag, 0x1)
        self.assertEqual(event.interrupt_capture, 0xfe)
        self.assertEqual(event.pin_num, 0)
        self.assertEqual(event.direction, self.direction)
        self.test_passed = True
        self.barrier.wait()

    def tearDown(self):
        self.listener.deactivate()
        pifacedigitalio.deinit()


if __name__ == "__main__":
    unittest.main()
