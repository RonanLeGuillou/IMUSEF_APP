#Embedded file name: openant/master/scripts/powertap_p1_tc.py
from __future__ import absolute_import, print_function
from ant.easy.node import Node
from ant.easy.channel import Channel
from ant.base.message import Message
import logging
import struct
import threading
import sys
import Tkinter as tk
import numpy as np
import array
import time
NETWORK_KEY = [185, 165, 33, 251, 189, 114, 195, 69]
POWER = 0

class Powertap:

    def __init__(self):
        self.node = Node()
        self.node.set_network_key(0, NETWORK_KEY)
        self.channel = self.node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)
        self.channel.on_broadcast_data = self.on_data
        self.channel.on_burst_data = self.on_data
        self.channel.set_period(8182)
        self.channel.set_search_timeout(30)
        self.channel.set_rf_freq(57)
        self.channel.set_id(54968, 11, 5)

        self.update_event_count = 0
        self.power = 0

        #self.datafile = open('/ptap.txt', 'w+')
        #self.datafile.write('time\tcadence\tpower\n')

    def on_data(self, data):
        page_number = format(data[0], '02X')
        if page_number == '10':
            if data[3] != 255 and data[1] != self.update_event_count:
                cadence = data[3]
                self.power = int(data[7] << 8 | data[6])
                self.update_event_count = data[1]
                print('Cadence : ' + str(cadence) + ' || Power : ' + str(self.power) + 'W' + ' (' + str(hex(data[6])) + '|' + str(hex(data[7])) + ')')
#                self.datafile.write(str(time.time()) + '\t' + str(cadence) + '\t' + str(self.power) + '\n')

        elif page_number == '13':
            print(str(data))
            if data[3] != 255 and data[2] != 255 and data[1] != self.update_event_count:
                right_torque = data[3] * 0.5
                left_torque = data[2] * 0.5
                self.update_event_count = data[1]
                print('Right Torque : ' + str(right_torque) + '% || Left Torque : ' + str(left_torque) + '%')
        elif page_number == '01':
            if data[1] == 172:
                print('Calibration Successful')
            elif data[1] == 175:
                print('Calibration Failed')
            if data[2] == 0:
                print('Autozero is OFF')
            elif data[2] == 1:
                print('Autozero is ON')
            elif data[2] == 255:
                print('Autozero is NOT SUPPORTED')
        elif page_number == '02':
            if data[1] == 1:
                print('Crank length : ' + str(data[4] * 0.5 + 110))
                sensor_status = bin(data[5])[2:10]
                sensor_capabilities = bin(data[6])[2:10]
                if sensor_status[-2:] == '00':
                    print('Crank length invalid')
                elif sensor_status[-2:] == '10':
                    print('Default crank length used')
                elif sensor_status[-2:] == '01':
                    print('Crank length set manually')
                elif sensor_status[-2:] == '11':
                    print('Crank length automatically set')
                print('Firmware status : ' + str(sensor_status[-4:-2]))
                print('Sensor avail. :' + str(sensor_status[-6:-4]))
                if sensor_status[0:2] == '00':
                    print('Custom calibration NA')
                if sensor_capabilities == '0':
                    print('Auto crank length NA')
        elif page_number == '52':
            print('Battery identifier:' + str(bin(data[2])[2:10]))
            print('Battery capacity(%) : ' + str(data[6] / 256.0 * 100))

    def start_node(self):
        self.node.start()

    def stop_node(self):
        self.node.stop()
        self.text.insert('1.0', 'NODE STOPPED')

    def auto_zero(self):
        self.text.insert('1.0', 'AUTO ZERO REQUEST')
        auto_zero_req = array.array('B', [1,
         171,
         1,
         255,
         255,
         255,
         255,
         255])
        self.channel.send_acknowledged_data(auto_zero_req)

    def manual_zero(self):
        self.text.insert('1.0', 'MANUAL ZERO REQUEST')
        man_zero_req = array.array('B', [1,
         170,
         255,
         255,
         255,
         255,
         255,
         255])
        self.channel.send_acknowledged_data(man_zero_req)

    def request(self):
        self.text.insert('1.0', 'REQUEST')
        self.channel.send_acknowledged_data(array.array('B', [70,
         255,
         255,
         1,
         0,
         0,
         2,
         1]))


def main():
    logging.basicConfig()
    powertap = Powertap()
    thread_node = threading.Thread(None, target=powertap.start_node)
    try:
        powertap.channel.open()
        thread_node.start()
        print('thread started')
    except:
        print('error')


if __name__ == '__main__':
    main()
