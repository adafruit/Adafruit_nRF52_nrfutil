# nrfutil

`nrfutil` is a Python package that includes the nrfutil command line utility
and the nordicsemi library.

This tool can be used used with the [Adafruit nRF52 Feather](https://www.adafruit.com/product/3406)
to flash firmware images onto the device using the simple serial port.

This library is written for Python 2.7.

# Installation

Run the following commands to make `nrfutil` available from the command line
or to development platforms like the Arduino IDE or CircuitPython:

```
$ sudo pip install -r requirements.txt
$ sudo python setup.py install
```

**Notes** : Do **NOT** install nrfutil from the pip package (ex. `sudo pip
install nrfutil`). The latest nrfutil does not support DFU via Serial, and you
should install the local copy of 0.5.2 included with the BSP via the `python
setup.py install` command above.

# Usage

To get info on usage of nrfutil:

```
nrfutil --help
```

To convert an nRF52 .hex file into a DFU pkg file that the serial bootloader
can make use of:

```
nrfutil dfu genpkg --dev-type 0x0052 --application firmware.hex dfu-package.zip
```

To flash a DFU pkg file over serial:

```
nrfutil dfu serial --package dfu-package.zip -p /dev/tty.SLAB_USBtoUART -b 115200
```
