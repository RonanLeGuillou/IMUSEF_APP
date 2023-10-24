#Embedded file name: openant/master/scripts/hearth_rate_monitor.py
from __future__ import absolute_import, print_function
from ant.easy.node import Node
from ant.easy.channel import Channel
#from easy.base.message import Message
import logging
import struct
import threading
import sys
import time
NETWORK_KEY = [185, 165, 33, 251, 189, 114, 195, 69]

class HRM:

    def __init__(self):
        self.hr_file = open('hr.txt', 'w+')

    def on_data(self, data):
        #self.hr_file = open('hr.txt', 'a')#/home/cybathlon/Bureau/Cybathlon/data_files/
        #self.hr_file.write(str(time.time()) + '\t' + str(data[7]) + '\n')
        string = 'Hearthrate: ' + str(data[7]) + '\n'
        sys.stdout.write(string)


def main():
    logging.basicConfig()
    hrm = HRM()
    node = Node()
    node.set_network_key(0, NETWORK_KEY)
    channel = node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)
    channel.on_broadcast_data = hrm.on_data
    channel.on_burst_data = hrm.on_data
    channel.set_period(8070)
    channel.set_search_timeout(12)
    channel.set_rf_freq(57)
    channel.set_id(0, 120, 0)
    try:
        channel.open()
        node.start()
    finally:
        node.stop()


if __name__ == '__main__':
    main()
