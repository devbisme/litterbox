# -*- coding: utf-8 -*-

# MIT license
# 
# Copyright (C) 2016 by { cookiecutter.full_name }
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import argparse as AP
import logging
import RPi.GPIO as GPIO
from .litterbox import *
from . import __version__

###############################################################################
# Command-line interface.
###############################################################################

def main():

    parser = AP.ArgumentParser(description='Configure the CAT Board FPGA with a bitstream file, or erase and program the CAT Board SPI flash.')
    parser.add_argument('-V', '--version', action='version', version='litterbox' + __version__)
    parser.add_argument('-e', '--erase', action='store_true', help='Erase flash.')
    parser.add_argument('-v', '--verify', nargs='?', type=str, metavar='file.bin', help='Verify flash contents against file.')
    parser.add_argument('-p', '--program', nargs='?', type=str, metavar='file.bin', help='Program flash with contents of file.')
    parser.add_argument('-c', '--configure', nargs='?', type=str, metavar='file.bin', help='Configure FPGA with contents of bitstream file.')
    parser.add_argument('-r', '--reset', action='store_true', help='Reset FPGA.')
    parser.add_argument('-d', '--debug', nargs='?', type=int, default=None, metavar='LEVEL', help='Print debugging info. (Larger LEVEL means more info.)')
    parser.add_argument('-t', '--test', nargs='?', type=str, metavar='file.bin', help='Run FPGA configuration test.')
    parser.add_argument('-s', '--speedtest', nargs='?', type=str, metavar='speed', help='Test SPI bitrate.')
    parser.add_argument('--enable', action='store_true', help='Wake flash from deep power-down state.')
    parser.add_argument('--disable', action='store_true', help='Put flash into deep power-down state.')
    parser.add_argument('--reset_pin', nargs='?', type=int, metavar='pin#', default=22, help='Specify FPGA reset GPIO pin number.')
    parser.add_argument('--done_pin', nargs='?', type=int, metavar='pin#', default=17, help='Specify FPGA configuration done GPIO pin number.')
    parser.add_argument('--cs_pin', nargs='?', type=int, metavar='pin#', default=25, help='Specify SPI flash chip-select GPIO pin number.')
    parser.add_argument('--clk_pin', nargs='?', type=int, metavar='pin#', default=11, help='Specify SPI flash clock GPIO pin number.')
    parser.add_argument('--mosi_pin', nargs='?', type=int, metavar='pin#', default=9, help='Specify SPI flash MOSI GPIO pin number.')
    parser.add_argument('--miso_pin', nargs='?', type=int, metavar='pin#', default=10, help='Specify SPI flash MISO GPIO pin number.')

    args = parser.parse_args()

    logger = logging.getLogger('litterbox')
    if args.debug is not None:
        log_level = logging.DEBUG + 1 - args.debug
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        logger.addHandler(handler)
        logger.setLevel(log_level)

    GPIO.setmode(GPIO.BCM)  # Broadcom pin-numbering scheme
    at25 = AT25SF041(args.clk_pin, args.cs_pin, args.mosi_pin, args.miso_pin)
    fpga = FPGA(args.reset_pin, args.done_pin, args.cs_pin)

    try:
        if args.reset:
            fpga.disable()
            fpga.enable()

        if args.erase:
            fpga.disable()
            at25.setup()
            at25.end_deep_power_down()
            at25.erase()
            at25.start_deep_power_down()
            fpga.enable()

        if args.program != None:
            fpga.disable()
            at25.setup()
            at25.end_deep_power_down()
            at25.erase()
            at25.program(args.program)
            at25.start_deep_power_down()
            fpga.enable()

        if args.verify != None:
            fpga.disable()
            at25.setup()
            at25.end_deep_power_down()
            at25.verify(args.verify)
            at25.start_deep_power_down()
            fpga.enable()

        if args.disable:
            fpga.disable()
            at25.setup()
            at25.start_deep_power_down()
            fpga.enable()

        if args.enable:
            fpga.disable()
            at25.setup()
            at25.end_deep_power_down()
            fpga.enable()

        if args.configure:
            at25.setup()
            at25.start_deep_power_down()
            fpga.configure(args.configure)

        if args.test:
            at25.start_deep_power_down()
            fpga.test(args.test)

        if args.speedtest:
            at25.start_deep_power_down()
            fpga.speed_test(int(args.speedtest) * 1000000)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()



###############################################################################
# Main entrypoint.
###############################################################################
if __name__ == '__main__':
    main()
