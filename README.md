# nrfutil

`nrfutil` is a Python package that includes the nrfutil command line utility
and the nordicsemi library.

This tool can be used used with the [Adafruit nRF52 Feather](https://www.adafruit.com/product/3406)
to flash firmware images onto the device using the simple serial port.

This library is written for Python 3.5+
It is no longer Python 2 compatible!

# Installation

Run the following commands to make `nrfutil` available from the command line
or to development platforms like the Arduino IDE or CircuitPython:

**Notes** : Do **NOT** install nrfutil from the pip package (ex. `sudo pip
install nrfutil`). The latest nrfutil does not support DFU via Serial, and you
should install version 0.5.x from a local copy of this repo via the methods
detailed below:

### OS X and Linux

To install in user space in your home directory:

```
$ cd Adafruit_nRF52_nrfutil
$ pip3 install -r requirements.txt
$ python3 setup.py install --user
```

If you get permission errors when running `pip3 install`, your `pip3` is older
or is set to try to install in the system directories. In that case use the
`--user` flag:

```
$ cd Adafruit_nRF52_nrfutil
$ pip3 install -r --user requirements.txt
$ python3 setup.py install --user
```

If you want to install in system directories:
```
$ cd Adafruit_nRF52_nrfutil
$ sudo pip3 install -r requirements.txt
$ sudo python3 setup.py install
```

Note: When installing requirements if you encounter issue **Cannot uninstall 'six'. It is a distutils installed project ...** . You may need to add `--ignore-installed six` when running pip.

### Windows

#### Option 1: Pre-Built Binary

A pre-built 32-bit version of adafruit_nrfutil.exe is included as part of this repo in the
`binaries/win32` folder. You can use this pre-built binary by adding it to your
systems `$PATH` variable

#### Option 2: Build nrfutil from Source

Make sure that you have **Python 3.5** available on your system.

To generate a self-contained Windows `.exe` version of the utility (Windows only),
run these commands in a CMD window:

```
pip3 install pyinstaller
cd Adafruit_nRF52_nrfuil
pip3 install -r requirements.txt
cd Adafruit_nRF52_nrfutil\nordicsemi
pyinstaller __main__.py --onefile --clean --name adafruit_nrfutil
```
You will find the .exe in `Adafruit_nRF52_nrfutil\nordicsemi\adafruit_nrfutil.exe`.
Copy or move it elsewhere for your convenience, such as directory in your %PATH%.

# Usage

To get info on usage of adafruit_nrfutil:

```
adafruit_nrfutil --help
```

To convert an nRF52 .hex file into a DFU pkg file that the serial bootloader
can make use of:

```
adafruit_nrfutil dfu genpkg --dev-type 0x0052 --application firmware.hex dfu-package.zip
```

To flash a DFU pkg file over serial:

```
adafruit_nrfutil dfu serial --package dfu-package.zip -p /dev/tty.SLAB_USBtoUART -b 115200
```
