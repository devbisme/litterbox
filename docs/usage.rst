========
Usage
========

litterbox lets you control the CAT Board from the Raspberry Pi.
You'll use it primarily to do three things:

#. Configure the FPGA on the CAT Board with a bitstream file like so:

        sudo litterbox -c filename.bin

#. Store a bitstream file into the CAT Board serial flash that will be loaded
   into the FPGA whenever the board is powered on or reset:

        sudo litterbox -p filename.bin

#. Erase the serial flash so the FPGA will no longer be configured by default:

        sudo litterbox -e

---------------------
Command-Line Options
---------------------

::

usage: litterbox [-h] [-V] [-e] [-v [file.bin]] [-p [file.bin]]
                 [-c [file.bin]] [-r] [-d [LEVEL]] [-t [file.bin]] [--enable]
                 [--disable] [--reset_pin [pin#]] [--done_pin [pin#]]
                 [--cs_pin [pin#]] [--clk_pin [pin#]] [--mosi_pin [pin#]]
                 [--miso_pin [pin#]]

Configure CAT Board FPGA with a bitstream file, or erase and program CAT Board SPI flash.

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -e, --erase           Erase flash.
  -v [file.bin], --verify [file.bin]
                        Verify flash contents against file.
  -p [file.bin], --program [file.bin]
                        Program flash with contents of file.
  -c [file.bin], --configure [file.bin]
                        Configure FPGA with contents of bitstream file.
  -r, --reset           Reset FPGA.
  -d [LEVEL], --debug [LEVEL]
                        Print debugging info. (Larger LEVEL means more info.)
  -t [file.bin], --test [file.bin]
                        Run FPGA configuration test.
  --enable              Wake flash from deep power-down state.
  --disable             Put flash into deep power-down state.
  --reset_pin [pin#]    Specify FPGA reset GPIO pin number.
  --done_pin [pin#]     Specify FPGA configuration done GPIO pin number.
  --cs_pin [pin#]       Specify SPI flash chip-select GPIO pin number.
  --clk_pin [pin#]      Specify SPI flash clock GPIO pin number.
  --mosi_pin [pin#]     Specify SPI flash MOSI GPIO pin number.
  --miso_pin [pin#]     Specify SPI flash MISO GPIO pin number.
