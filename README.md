# adafruit-nrfutil

`adafruit-nrfutil` is a Python package that includes the `adafruit-nrfutil` command line utility
and the `nordicsemi` library.

This package is derived from the Nordic Semiconductor ASA package
[pc-nrfutil](https://github.com/NordicSemiconductor/pc-nrfutil), version 0.5.3.
The code has been converted from Python 2 to Python 3.

The executable `nrfutil` has been renamed to `adafruit-nrfutil` to distinguish it from the
original executable.

This tool can be used with the [Adafruit nRF52 Feather](https://www.adafruit.com/product/3406)
to flash firmware images onto the device using the simple serial port.

This library is written for Python 3.5+. It is no longer Python 2 compatible!

# Installation

## Prerequisites

- Python3
- pip3

Run the following commands to make `adafruit-nrfutil` available from the command line
or to development platforms like the Arduino IDE or CircuitPython:

## Installing from PyPI

This is recommended method, to install latest version

```
$ pip3 install --user adafruit-nrfutil
```

## Installing from Source

Use this method if you have issue installing with PyPi or want to modify the tool. First clone this repo and go into its folder.

```
$ git clone https://github.com/adafruit/Adafruit_nRF52_nrfutil.git
$ cd Adafruit_nRF52_nrfutil
```

Note: following commands use `python3`, however if you are on Windows, you may need to change it to `python` since windows installation of python 3.x still uses the name python.exe

To install in user space in your home directory:

```
$ pip3 install -r requirements.txt
$ python3 setup.py install
```

If you get permission errors when running `pip3 install`, your `pip3` is older
or is set to try to install in the system directories. In that case use the
`--user` flag:

```
$ pip3 install -r --user requirements.txt
$ python3 setup.py install
```

If you want to install in system directories (generally not recommended):
```
$ sudo pip3 install -r requirements.txt
$ sudo python3 setup.py install
```

### Create self-contained binary

To generate a self-contained executable binary of the utility (Windows and MacOS), run these commands:

```
pip3 install pyinstaller
cd Adafruit_nRF52_nrfutil
pip3 install -r requirements.txt
cd Adafruit_nRF52_nrfutil\nordicsemi
pyinstaller __main__.py --onefile --clean --name adafruit-nrfutil
```
You will find the .exe in `Adafruit_nRF52_nrfutil\nordicsemi\dist\adafruit-nrfutil` ( with `.exe` if you are on windows).
Copy or move it elsewhere for your convenience, such as directory in your %PATH%.

# Usage

To get info on the usage of adafruit-nrfutil:

```
adafruit-nrfutil --help
```

To convert an nRF52 .hex file into a DFU pkg file that the serial bootloader
can make use of:

```
adafruit-nrfutil dfu genpkg --dev-type 0x0052 --application firmware.hex dfu-package.zip
```

To flash a DFU pkg file over serial:

```
adafruit-nrfutil dfu serial --package dfu-package.zip -p /dev/tty.SLAB_USBtoUART -b 115200
```
