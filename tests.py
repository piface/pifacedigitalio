#!/usr/bin/env python3
"""Some basic tests, could do with improving"""
import unittest
import pifacecommon
import pifacedigitalio


LED_RANGE = 8
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
            self.assertRaises(pifacecommon.core.RangeError, self.item_type, i)


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
        # function is supposed to return 1
        pifacecommon.read_bit = lambda pin, port, board: 1

    def test_flip_bit(self):
        # should flip 1 to 0
        self.assertEqual(pifacedigitalio.digital_read(0, 0), 0)


if __name__ == "__main__":
    unittest.main()
