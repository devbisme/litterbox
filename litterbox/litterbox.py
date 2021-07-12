# -*- coding: utf-8 -*-

# MIT license, Copyright (C) 2016-2021 by Dave Vandenbout.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import sys
import logging
from copy import deepcopy
from pprint import pprint
import RPi.GPIO as GPIO
import array as ARRAY
import tqdm
import time
import os.path
import subprocess as SP

import spi as SPI

logger = logging.getLogger('litterbox')

USING_PYTHON2 = (sys.version_info.major == 2)
USING_PYTHON3 = not USING_PYTHON2

DEBUG_OVERVIEW = logging.DEBUG
DEBUG_DETAILED = logging.DEBUG - 1
DEBUG_OBSESSIVE = logging.DEBUG - 2


class Pin:
    def __init__(self, pin_num, direction=GPIO.IN, init_value=0):
        self.setup(pin_num, direction, init_value)

    def setup(self, pin_num, direction=GPIO.IN, init_value=0):
        self.pin_num = pin_num
        self.direction = direction
        GPIO.setup(self.pin_num, self.direction)
        self.output(init_value)

    def output(self, value=0):
        def limit(v):
            if v > 0:
                return GPIO.HIGH
            else:
                return GPIO.LOW

        if self.direction == GPIO.OUT:
            self.value = limit(value)
            GPIO.output(self.pin_num, value)

    def input(self):
        if self.direction == GPIO.OUT:
            return self.value
        elif self.direction == GPIO.IN:
            self.value = GPIO.input(self.pin_num)
            return self.value
        else:
            raise exception(
                'Reading pin {0} which is neither an input or output.'.format(
                    self.pin_num))


class SoftSpi:
    def __init__(self, clk_pin, cs_pin, mosi_pin, miso_pin):
        self.clk_pin = clk_pin
        self.cs_pin = cs_pin
        self.mosi_pin = mosi_pin
        self.miso_pin = miso_pin
        self.setup()

    def setup(self):
        self.clk = Pin(self.clk_pin, GPIO.OUT, 0)
        self.cs = Pin(self.cs_pin, GPIO.OUT, 1)
        self.mosi = Pin(self.mosi_pin, GPIO.OUT, 0)
        self.miso = Pin(self.miso_pin, GPIO.IN)

    def enable(self):
        self.cs.output(0)

    def disable(self):
        self.cs.output(1)

    def send_rcv(self, num_bits=8, out_value=0):
        mask = 1 << (num_bits-1)
        in_value = 0
        clk_out = self.clk.output
        mosi_out = self.mosi.output
        miso_in = self.miso.input
        for _ in range(num_bits):
            mosi_out(out_value & mask)
            mask = mask >> 1
            clk_out(1)
            in_value = (in_value << 1) | miso_in()
            clk_out(0)
        return in_value


class AT25SF041:
    READ_DEVICE_ID_OP = 0x9F
    LEGACY_READ_DEVICE_ID_OP = 0x90
    START_DEEP_POWER_DOWN_OP = 0xB9
    END_DEEP_POWER_DOWN_OP = 0xAB
    READ_ARRAY_OP = 0x03
    CHIP_ERASE_OP = 0x60
    PROGRAM_OP = 0x02
    READ_STATUS1_OP = 0x05
    READ_STATUS2_OP = 0x35
    WRITE_ENABLE_OP = 0x06
    WRITE_DISABLE_OP = 0x04
    PAGE_PROGRAM_OP = 0x02

    OPCODE_LENGTH = 8
    MANF_ID_LENGTH = 8
    DEVICE_ID_LENGTH = 16
    LEGACY_DEVICE_ID_LENGTH = 8
    ADDRESS_LENGTH = 24
    DATA_LENGTH = 8
    STATUS_LENGTH = 8
    PAGE_LENGTH = 256
    PAGE_ADDRESS_MASK = 0xFFFF00

    def __init__(self, clk_pin, cs_pin, mosi_pin, miso_pin):
        self.spi = SoftSpi(clk_pin, cs_pin, mosi_pin, miso_pin)

    def setup(self):
        self.spi.setup()

    def read_device_id(self):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.READ_DEVICE_ID_OP)
        manf_id = self.spi.send_rcv(self.MANF_ID_LENGTH)
        device_id = self.spi.send_rcv(self.DEVICE_ID_LENGTH)
        self.spi.disable()
        return manf_id, device_id

    def legacy_read_device_id(self):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.LEGACY_READ_DEVICE_ID_OP)
        self.spi.send_rcv(24, 0)
        manf_id = self.spi.send_rcv(self.MANF_ID_LENGTH)
        device_id = self.spi.send_rcv(self.LEGACY_DEVICE_ID_LENGTH)
        self.spi.disable()
        return manf_id, device_id

    def read_status1(self):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.READ_STATUS1_OP)
        status1 = self.spi.send_rcv(self.STATUS_LENGTH)
        self.spi.disable()
        return status1

    def read_status2(self):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.READ_STATUS2_OP)
        status2 = self.spi.send_rcv(self.STATUS_LENGTH)
        self.spi.disable()
        return status2

    def read_status(self):
        return self.read_status1(), self.read_status2()

    def is_busy(self):
        return self.read_status1() & 1

    def enable_write(self):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.WRITE_ENABLE_OP)
        self.spi.disable()

    def disable_write(self):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.WRITE_DISABLE_OP)
        self.spi.disable()

    def start_deep_power_down(self):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.START_DEEP_POWER_DOWN_OP)
        self.spi.disable()
        if self.read_device_id() == (0x1F, 0x8401):
            print('Deep power down failed!')
        else:
            print('Flash is in deep power down state.')

    def end_deep_power_down(self):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.END_DEEP_POWER_DOWN_OP)
        self.spi.disable()
        if self.read_device_id() == (0x1F, 0x8401):
            print('Flash is powered on!')
        else:
            print('Wake from deep power down failed.')

    def read_array(self, address, num_bytes):
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.READ_ARRAY_OP)
        self.spi.send_rcv(self.ADDRESS_LENGTH, address)
        array = list()
        for i in tqdm.tqdm(range(num_bytes)):
            array.append(self.spi.send_rcv(self.DATA_LENGTH))
        self.spi.disable()
        return array

    def erase(self):
        self.enable_write()
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.CHIP_ERASE_OP)
        self.spi.disable()
        while self.is_busy():
            pass

    def write_page(self, address, array):
        self.enable_write()
        self.spi.enable()
        self.spi.send_rcv(self.OPCODE_LENGTH, self.PAGE_PROGRAM_OP)
        self.spi.send_rcv(self.ADDRESS_LENGTH, address)
        for b in array:
            self.spi.send_rcv(self.DATA_LENGTH, b)
        self.spi.disable()
        while self.is_busy():
            pass

    def write_array(self, start_address, array):
        end_address = start_address + len(array) - 1
        address1 = start_address
        index = 0
        with tqdm.tqdm(total=end_address+1-start_address, unit=' bytes', ascii=True) as pbar:
            while address1 <= end_address:
                address2 = (address1 + self.PAGE_LENGTH) & self.PAGE_ADDRESS_MASK
                num_bytes = address2 - address1
                page_array = array[index:index+num_bytes]
                self.write_page(address1, page_array)
                address1 = address2
                index += num_bytes
                pbar.update(num_bytes)

    def program(self, filename):
        try:
            with open(filename, 'rb') as file:
                array = bytearray(file.read())
                self.write_array(0, array)
        except IOError:
            pass

class HardSpi:
    def __init__(self):
        for spi_module in ['spi_bcm2708', 'spi_bcm2835']:
            if not SP.call(['modprobe', '-q', spi_module]):
                self.spi_module = spi_module
                break
        else:
            raise Exception('Unable to load SPI module!')
        self.setup()

    def setup(self):
        SP.call(['modprobe', '-r', self.spi_module])
        SP.call(['modprobe', self.spi_module])
        self.spi = SPI.SPI('/dev/spidev0.0')
        self.spi.mode = SPI.SPI.MODE_0
        self.spi.bits_per_word = 8
        self.spi.speed = 100000000

    def set_speed(self, speed):
        self.spi.speed = speed

    def write(self, data):
        self.spi.write(data)
        return

class FPGA:
    def __init__(self, reset_pin, done_pin, cs_pin):
        self.setup(reset_pin, done_pin, cs_pin)

    def setup(self, reset_pin, done_pin, cs_pin):
        self.reset = Pin(reset_pin, GPIO.OUT, 0)
        self.done = Pin(done_pin, GPIO.IN)
        self.cs = Pin(cs_pin, GPIO.OUT, 1)
        self.spi = HardSpi()

    def is_configured(self):
        return self.done.input() is True

    def enable(self):
        self.reset.output(1)

    def disable(self):
        self.reset.output(0)

    def configure(self, file):
        self.disable()
        self.cs.output(0)
        self.enable()
        self.spi.setup()
        try:
            length = os.path.getsize(file)
            with open(file, 'rb') as f:
                bits = ARRAY.array(str('B'))
                try:
                    bits.fromfile(f,length)
                except EOFError:
                    pass
                bits.fromlist([0] * 7)
                self.spi.write(bits)
        except IOError:
            print('IOError reading', file)
        print('FPGA configuration complete!' if self.done.input() else 'FPGA NOT CONFIGURED!')

    def test(self, file):
        try:
            while True:
                self.configure(file)
                print(time.time())
        except KeyboardInterrupt:
            pass

    def speed_test(self, speed):
        self.spi.set_speed(speed)
        data = bytes(list(range(256)) * 4096 * 10)
        num_bits = 8 * len(data)
        tot_time = 0
        tot_bits = 0
        try:
            while True:
                start = time.time()
                self.spi.write(data)
                end = time.time()
                tot_bits += num_bits
                tot_time += (end-start)
                print('bit rate = {} ({})'.format(num_bits / (end-start), tot_bits/tot_time))
        except KeyboardInterrupt:
            pass
