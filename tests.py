#!/usr/bin/env python3
"""Some basic tests, could do with improving"""
import unittest
import pifacecommon as pfcom
import pifacedigitalio as pfdio


class TestRangedItem(object):
    def test_normal_init(self):
        for i in self.item_range:
            led = self.item(i)
            self.assertEqual(type(led), self.item)

    def test_boundary_init(self):
        for i in (min(self.item_range)-1, max(self.item_range)+1):
            self.assertRaises(pfcom.RangeError, self.item, i)


class TestLED(TestRangedItem, unittest.TestCase):
    item = pfdio.LED
    item_range = range(8)


class TestSwitch(TestRangedItem, unittest.TestCase):
    item = pfdio.Switch
    item_range = range(4)


class TestRelay(TestRangedItem, unittest.TestCase):
    item = pfdio.Relay
    item_range = range(2)


class TestDigitalRead(unittest.TestCase):
    def setUp(self):
        pfdio.pfcom.read_bit = lambda pin, port, board: 1  # function returns 1

    def test_flip_bit(self):
        self.assertEqual(pfdio.digital_read(0, 0), 0)  # should return 0


if __name__ == "__main__":
    unittest.main()
