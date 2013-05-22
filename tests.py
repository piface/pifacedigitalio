#!/usr/bin/env python3
"""Some basic tests, could do with improving"""
import unittest
import pifacedigitalio as pfdio


class TestRangedItem(object):
    def test_normal_init(self):
        for i in self.item_range:
            led = self.item(i)
            self.assertEqual(type(led), self.item)

    def test_boundary_init(self):
        for i in (min(self.item_range)-1, max(self.item_range)+1):
            self.assertRaises(pfdio.RangeError, self.item, i)


class TestLED(TestRangedItem, unittest.TestCase):
    item = pfdio.LED
    item_range = range(8)


class TestSwitch(TestRangedItem, unittest.TestCase):
    item = pfdio.Switch
    item_range = range(4)


class TestRelay(TestRangedItem, unittest.TestCase):
    item = pfdio.Relay
    item_range = range(2)


class TestItem(unittest.TestCase):
    def test_item_normal_board_init(self):
        for i in range(pfdio.MAX_BOARDS):
            item = pfdio.Item(0, i)
            self.assertEqual(type(item), pfdio.Item)

    def test_item_boundary_board_init(self):
        for i in (-1, pfdio.MAX_BOARDS):
            with self.assertRaises(pfdio.RangeError):
                pfdio.Item(0, i)


class TestDigitalRead(unittest.TestCase):
    def setUp(self):
        pfdio.pfcom.read_bit = lambda pin, port, board: 1  # function returns 1

    def test_flip_bit(self):
        self.assertEqual(pfdio.digital_read(0, 0), 0)  # should return 0


if __name__ == "__main__":
    unittest.main()
