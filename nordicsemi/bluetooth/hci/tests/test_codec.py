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

import json
import unittest
from nordicsemi.bluetooth.hci.slip import Slip
from nordicsemi.bluetooth.hci import codec


class TestInitPacket(unittest.TestCase):
    def setUp(self):
        pass

    def test_decode_packet(self):
        # TODO: extend this test, this tests only a small portion of the slip/hci decoding
        # These are packets read from Device Monitoring Studio
        # during communication between serializer application and firmware
        read_packets = [
            b'\xC0\x10\x00\x00\xF0\xC0\xC0\xD1\x6E\x00\xC1\x01\x86\x00\x00\x00\x00\x17\x63\xC0',
            b'\xC0\xD2\xDE\x02\x4E\x02\x1B\x00\xFF\xFF\x01\x17\xFE\xB4\x9A\x9D\xE1\xB0\xF8\x02'
            b'\x01\x06\x11\x07\x1B\xC5\xD5\xA5\x02\x00\xA9\xB7\xE2\x11\xA4\xC6\x00\xFE\xE7\x74'
            b'\x09\x09\x49\x44\x54\x57\x32\x31\x38\x48\x5A\xBB\xC0',
            b'\xC0\xD3\xEE\x00\x3F\x02\x1B\x00\xFF\xFF\x01\x17\xFE\xB4\x9A\x9D\xE1\xAF\x01\xF1\x62\xC0',
            b'\xC0\xD4\xDE\x02\x4C\x02\x1B\x00\xFF\xFF\x01\x17\xFE\xB4\x9A\x9D\xE1\xB1\xF8\x02\x01\x06'
            b'\x11\x07\x1B\xC5\xD5\xA5\x02\x00\xA9\xB7\xE2\x11\xA4\xC6\x00\xFE\xE7\x74\x09\x09\x49\x44\x54\x57\x32\x31\x38\x48\x6E\xC8\xC0'
        ]

        slip = Slip()
        output = list()

        for uart_packet in read_packets:
            slip.append(uart_packet)

        packets = slip.decode()

        for packet in packets:
            output.append(codec.ThreeWireUartPacket.decode(packet))

        self.assertEqual(len(output), 5)

        packet_index = 0
        self.assertEqual(output[packet_index].seq, 0)

        packet_index += 1
        self.assertEqual(output[packet_index].seq, 1)

        packet_index += 1
        self.assertEqual(output[packet_index].seq, 2)

        packet_index += 1
        self.assertEqual(output[packet_index].seq, 3)

        packet_index += 1
        self.assertEqual(output[packet_index].seq, 4)
