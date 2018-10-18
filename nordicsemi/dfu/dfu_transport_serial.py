# Copyright (c) 2015, Nordic Semiconductor
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of Nordic Semiconductor ASA nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Python imports
import time
from datetime import datetime, timedelta
import binascii
import logging
import click

# Python 3rd party imports
from serial import Serial

# Nordic Semiconductor imports
from nordicsemi.dfu.util import slip_parts_to_four_bytes, slip_encode_esc_chars, int16_to_bytes, int32_to_bytes
from nordicsemi.dfu import crc16
from nordicsemi.exceptions import NordicSemiException
from nordicsemi.dfu.dfu_transport import DfuTransport, DfuEvent


logger = logging.getLogger(__name__)


class DfuTransportSerial(DfuTransport):

    DEFAULT_BAUD_RATE = 115200
    DEFAULT_FLOW_CONTROL = False
    DEFAULT_SERIAL_PORT_TIMEOUT = 1.0  # Timeout time on serial port read
    SERIAL_PORT_OPEN_WAIT_TIME = 0.1
    TOUCH_RESET_WAIT_TIME = 1.5     # Wait time for device into DFU mode
    DTR_RESET_WAIT_TIME = 0.1
    ACK_PACKET_TIMEOUT = 1.0  # Timeout time for for ACK packet received before reporting timeout through event system

    # ADADFRUIT:
    # - After Start packet is sent, nrf5x will start to erase flash page, each page takes 2.05 - 89.7 ms
    # nrfutil need to wait accordingly for the image size
    # - (dual bank only) After sending all data -> send command to activate new firmware --> nrf52 erase bank0 and copy image
    # from bank1 to bank0. nrfutil need to wait else IDE will re-open serial --> causing pin reset -> flash corruption.

    FLASH_PAGE_SIZE = 4096

    # Time to erase a page for nrf52832 is (2.05 to 89.7 ms), nrf52840 is ~85 ms max
    FLASH_PAGE_ERASE_TIME = 0.0897

    # Ttime to write word for nrf52832 is (67.5 to 338 us), nrf52840 is ~41 us max
    FLASH_WORD_WRITE_TIME = 0.000100

    # Time to write a whole page
    FLASH_PAGE_WRITE_TIME = (FLASH_PAGE_SIZE/4) * FLASH_WORD_WRITE_TIME

    # The DFU packet max size
    DFU_PACKET_MAX_SIZE = 512

    def __init__(self, com_port, baud_rate=DEFAULT_BAUD_RATE, flow_control=DEFAULT_FLOW_CONTROL, single_bank=False, touch=0, timeout=DEFAULT_SERIAL_PORT_TIMEOUT):
        super(DfuTransportSerial, self).__init__()
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.flow_control = 1 if flow_control else 0
        self.single_bank = single_bank
        self.touch = touch
        self.timeout = timeout
        self.serial_port = None
        self.total_size = 167936 # default is max application size
        self.sd_size   = 0
        """:type: serial.Serial """


    def open(self):
        super(DfuTransportSerial, self).open()

        # Touch is enabled, disconnect and reconnect
        if self.touch > 0:
            try:
                touch_port = Serial(port=self.com_port, baudrate=self.touch, rtscts=self.flow_control, timeout=self.timeout)
            except Exception as e:
                raise NordicSemiException("Serial port could not be opened on {0}. Reason: {1}".format(self.com_port, e))

            # Wait for serial port stable
            time.sleep(DfuTransportSerial.SERIAL_PORT_OPEN_WAIT_TIME)

            touch_port.close()
            logger.info("Touched serial port %s", self.com_port)

            # Wait for device go into DFU mode and fully enumerated
            time.sleep(DfuTransportSerial.TOUCH_RESET_WAIT_TIME)

        try:
            self.serial_port = Serial(port=self.com_port, baudrate=self.baud_rate, rtscts=self.flow_control, timeout=self.timeout)
        except Exception as e:
            raise NordicSemiException("Serial port could not be opened on {0}. Reason: {1}".format(self.com_port, e))

        logger.info("Opened serial port %s", self.com_port)

        # Wait for serial port stable
        time.sleep(DfuTransportSerial.SERIAL_PORT_OPEN_WAIT_TIME)

        # Toggle DTR to reset the board and enter DFU mode (only if touch is not used)
        if self.touch == 0:
            self.serial_port.setDTR(False)
            time.sleep(0.05)
            self.serial_port.setDTR(True)

            # Delay to allow device to boot up
            time.sleep(DfuTransportSerial.DTR_RESET_WAIT_TIME)

    def close(self):
        super(DfuTransportSerial, self).close()
        self.serial_port.close()

    def is_open(self):
        super(DfuTransportSerial, self).is_open()

        if self.serial_port is None:
            return False

        return self.serial_port.isOpen()

    def send_validate_firmware(self):
        super(DfuTransportSerial, self).send_validate_firmware()
        return True

    def send_init_packet(self, init_packet):
        super(DfuTransportSerial, self).send_init_packet(init_packet)

        frame = [x for x in int32_to_bytes(DFU_INIT_PACKET)]
        frame += [chr(x) for x in bytes(init_packet)]
        frame += [x for x in int16_to_bytes(0x0000)]  # Padding required

        packet = HciPacket(frame)
        self.send_packet(packet)

    def get_erase_wait_time(self):
        # timeout is not least than 0.5 seconds
        return max(0.5, ((self.total_size // self.FLASH_PAGE_SIZE) + 1)*self.FLASH_PAGE_ERASE_TIME)

    def get_activate_wait_time(self):
        if (self.single_bank and (self.sd_size == 0)):
            # Single bank and not updating SD+Bootloader, we can skip bank1 -> bank0 delay
            # but still need to delay bootloader setting save (1 flash page)
            return self.FLASH_PAGE_ERASE_TIME + self.FLASH_PAGE_WRITE_TIME;
        else:
            # Activate wait time including time to erase bank0 and transfer bank1 -> bank0
            write_wait_time = ((self.total_size // self.FLASH_PAGE_SIZE) + 1) * self.FLASH_PAGE_WRITE_TIME
            return self.get_erase_wait_time() + write_wait_time

    def send_start_dfu(self, mode, softdevice_size=None, bootloader_size=None, app_size=None):
        super(DfuTransportSerial, self).send_start_dfu(mode, softdevice_size, bootloader_size, app_size)

        frame = [x for x in int32_to_bytes(DFU_START_PACKET)]
        frame += [x for x in int32_to_bytes(mode)]
        frame += [x for x in DfuTransport.create_image_size_packet(softdevice_size, bootloader_size, app_size)]

        packet = HciPacket(frame)
        self.send_packet(packet)

        self.sd_size = softdevice_size
        self.total_size = softdevice_size+bootloader_size+app_size
        #logger.info("Wait after Init Packet %s second", self.get_erase_wait_time())
        time.sleep( self.get_erase_wait_time() )

    def send_activate_firmware(self):
        super(DfuTransportSerial, self).send_activate_firmware()

        # Dual bank bootloader will erase the bank 0 with Application size & Transfer App size from bank1 to bank0
        # There must a enough delay before finished to prevent Arduino IDE reopen Serial Monitor which cause pin reset
        # Single bank bootloader could skip this delay if package contains only application firmware
        click.echo("\nActivating new firmware")

    def send_firmware(self, firmware):
        super(DfuTransportSerial, self).send_firmware(firmware)

        def progress_percentage(part, whole):
            return int(100 * float(part)/float(whole))

        frames = []
        self._send_event(DfuEvent.PROGRESS_EVENT, progress=0, done=False, log_message="")

        for i in range(0, len(firmware), DfuTransportSerial.DFU_PACKET_MAX_SIZE):
            theframe = [x for x in int32_to_bytes(DFU_DATA_PACKET)]
            theframe += [chr(x) for x in firmware[i:i + DfuTransportSerial.DFU_PACKET_MAX_SIZE]]
            data_packet = HciPacket(theframe)
            frames.append(data_packet)

        frames_count = len(frames)

        # Send firmware packets
        for count, pkt in enumerate(frames):
            self.send_packet(pkt)
            self._send_event(DfuEvent.PROGRESS_EVENT,
                             log_message="",
                             progress=count,
                             done=False)

            # After 8 frames (4096 Bytes), nrf5x will erase and write to flash. While erasing/writing to flash
            # nrf5x's CPU is blocked. We better wait a few ms, just to be safe
            if count%8 == 0:
                time.sleep(DfuTransportSerial.FLASH_PAGE_WRITE_TIME)

        # Wait for last page to write
        time.sleep(DfuTransportSerial.FLASH_PAGE_WRITE_TIME)

        # Send data stop packet
        frame = int32_to_bytes(DFU_STOP_DATA_PACKET)
        packet = HciPacket(frame)
        self.send_packet(packet)

        self._send_event(DfuEvent.PROGRESS_EVENT, progress=100, done=False, log_message="")

    def send_packet(self, pkt):
        attempts = 0
        last_ack = None
        packet_sent = False

        while not packet_sent:
            logger.debug("PC -> target: %s" % pkt)
            self.serial_port.write(bytearray(pkt.data))
            attempts += 1
            ack = self.get_ack_nr()

            if last_ack is None:
                break

            if ack == (last_ack + 1) % 8:
                last_ack = ack
                packet_sent = True

                if attempts > 3:
                    raise Exception("Three failed tx attempts encountered on packet {0}".format(pkt.sequence_number))

    def get_ack_nr(self):
        def is_timeout(start_time, timeout_sec):
            return not (datetime.now() - start_time <= timedelta(0, timeout_sec))

        uart_buffer = []
        start = datetime.now()

        while uart_buffer.count(0xC0) < 2:
            # Disregard first of the two C0
            temp = [x for x in self.serial_port.read(6)]

            if temp:
                uart_buffer += temp

            if is_timeout(start, DfuTransportSerial.ACK_PACKET_TIMEOUT):
                # reset HciPacket numbering back to 0
                HciPacket.sequence_number = 0
                self._send_event(DfuEvent.TIMEOUT_EVENT,
                                 log_message="Timed out waiting for acknowledgement from device.")

                # quit loop
                break

                # read until you get a new C0
                # RESUME_WORK

        if len(uart_buffer) < 2:
            raise NordicSemiException("No data received on serial port. Not able to proceed.")

        logger.debug("PC <- target: %s", [hex(i) for i in uart_buffer])
        data = self.decode_esc_chars(uart_buffer)

        # Remove 0xC0 at start and beginning
        data = data[1:-1]

        # Extract ACK number from header
        return (data[0] >> 3) & 0x07

    @staticmethod
    def decode_esc_chars(data):
        """Replace 0xDBDC with 0xCO and 0xDBDD with 0xDB"""
        result = []

        #data = bytearray(data)

        while len(data):
            char = data.pop(0)

            if char == 0xDB:
                char2 = data.pop(0)

                if char2 == 0xDC:
                    result.append(0xC0)
                elif char2 == 0xDD:
                    result.append(0xDB)
                else:
                    raise Exception('Char 0xDB NOT followed by 0xDC or 0xDD')
            else:
                result.append(char)

        return result

DATA_INTEGRITY_CHECK_PRESENT = 1
RELIABLE_PACKET = 1
HCI_PACKET_TYPE = 14

DFU_INIT_PACKET = 1
DFU_START_PACKET = 3
DFU_DATA_PACKET = 4
DFU_STOP_DATA_PACKET = 5

DFU_UPDATE_MODE_NONE = 0
DFU_UPDATE_MODE_SD = 1
DFU_UPDATE_MODE_BL = 2
DFU_UPDATE_MODE_APP = 4


class HciPacket(object):
    """Class representing a single HCI packet"""

    sequence_number = 0

    def __init__(self, data=''):
        HciPacket.sequence_number = (HciPacket.sequence_number + 1) % 8
        temp_data = []
        logger.debug("Data "+str(len(data))+": %s", data)
        slip_bytes = slip_parts_to_four_bytes(HciPacket.sequence_number,
                                                   DATA_INTEGRITY_CHECK_PRESENT,
                                                   RELIABLE_PACKET,
                                                   HCI_PACKET_TYPE,
                                                   len(data))
        temp_data += [ord(x) for x in slip_bytes]        
        logger.debug("Add slip preamble: %s", [hex(i) for i in temp_data])

        temp_data += [ord(x) for x in data]
        logger.debug("Add Data: %s", [hex(i) for i in temp_data])
        
        # Add escape characters
        crc = crc16.calc_crc16(bytes(temp_data) , crc=0xffff)
        logger.debug("CRC: %s", hex(crc))
        temp_data.append(crc & 0xFF)
        temp_data.append((crc & 0xFF00) >> 8)
        logger.debug("Add CRC: %s", [hex(i) for i in temp_data])

        encoded = slip_encode_esc_chars("".join(chr(x) for x in bytearray(temp_data)))
        temp_data = [ord(x) for x in encoded]
        logger.debug("SLIP encoded: %s", [hex(i) for i in temp_data])
        
        self.data = [0xc0]
        self.data += temp_data
        self.data += [0xc0]
        logger.debug("Final packet: %s", [hex(i) for i in self.data])

    def __str__(self):
        return str([hex(i) for i in self.data])
