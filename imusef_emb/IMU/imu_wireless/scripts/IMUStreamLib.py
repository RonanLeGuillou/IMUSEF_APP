#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# IMU Stream data library
# Copyright (C) 2015 HIKOB. All rights reserved.
# 
# Created on : Jan 10 2016
# Author : Matthieu Lauzier <matthieu.lauzier.at.hikob.com>
#

import os, sys, random
import datetime
import codecs
import struct
import datetime

## ##################################################
## ##################################################

class IMUStreamLog:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    log_level = 4 # 0: no messages, 1:error, 2: +warn, 3: +info, 4: +debug
    color = True
    quiet = False
    
    def disable(self):
        self.GREEN = ''
        self.BLUE = ''
        self.ORANGE = ''
        self.RED = ''
        self.ENDC = ''

    def __init__(self, ll, c, f=''):
        self.log_level = ll
        self.color = c
        if f is not '':
            self.fid = open(f, 'a')
        else:
            self.fid = None
        
    def setQuiet(self, q):
        self.quiet = q
                
    # Define the log function (print to stderr)
    def log(self, message, col):
        if not self.quiet:
            if self.fid is None:
                if self.color:
                    sys.stdout.write(col + message + self.ENDC + "\n")
                else:
                    sys.stderr.write(message + "\n")
                sys.stderr.flush()
            else:
                self.fid.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ": [OA] : ")
                if isinstance(message, str):
                    s = message
                elif isinstance(message, unicode):
                    s = message.encode('utf8')
                else:
                    print("not a string")
                self.fid.write(s)
                self.fid.write("\n")
                self.fid.flush()
                
                
    def __del__(self):
        if self.fid is not None:
            self.fid.close()
        
    def log_error(self, message):
        if self.log_level > 0:
            self.log(message, self.RED)

    def log_warn(self, message):
        if self.log_level > 1:
            self.log(message, self.ORANGE)
            
    def log_info(self, message):
        if self.log_level > 2:
            self.log(message, self.BLUE)
            
    def log_debug(self, message):
        if self.log_level > 3:
            self.log(message, self.GREEN)
            
## ##################################################
## ##################################################

class IMUStreamFormatFloat(float):
    def __repr__(self):
        return '%.04g' % self
    
class IMUStreamPacket:

    HDR_OFFSET = 4
    SIZE_AHRS  = 16
    SIZE_RAW   = 40
    
    def __init__(self):
        # Initialize variables
        self.src = 0
        self.seq = 0
        self.tfull    = 0
        self.bank     = 0
        self.attitude = 0
        self.heading  = 0
        self.traw     = 0
        self.acc = [0, 0, 0]
        self.mag = [0, 0, 0]
        self.gyr = [0, 0, 0]
        self.ok  = False
        self.ahrs = False
        self.raw  = False
        
    def parse(self, data, size, payloads):
        sdata = "".join(chr(i) for i in data)

        self.src, self.seq = struct.unpack('<HH', sdata[0:self.HDR_OFFSET])
        
        if size == payloads[0]+2:
            self.ahrs = True
            self.parse_ahrs(sdata[self.HDR_OFFSET:len(sdata)])
        elif size == payloads[1]+2:
            self.raw  = True
            self.parse_raw(sdata[self.HDR_OFFSET:len(sdata)])
        elif size == payloads[2]+2:
            self.ahrs = True
            self.raw  = True
            self.parse_full(sdata[self.HDR_OFFSET:len(sdata)])
            

    def parse_error(self):
        print("parse error")

    def parse_raw(self, data):
        self.traw, \
        self.acc[0], self.acc[1], self.acc[2], \
        self.mag[0], self.mag[1], self.mag[2], \
        self.gyr[0], self.gyr[1], self.gyr[2] = struct.unpack('<ffffffffff', data)
        if self.traw > 0:
            self.ok = True
        else:
            self.ok = False

    def parse_ahrs(self, data):
        self.tfull, \
        self.bank, self.attitude, self.heading = struct.unpack('<ffff', data)
        if self.tfull > 0:
            self.ok = True
        else:
            self.ok = False

    def parse_full(self, data):
        self.parse_ahrs(data[0:self.SIZE_AHRS])
        self.parse_raw (data[self.SIZE_AHRS:self.SIZE_AHRS+self.SIZE_RAW])
        
    def print_packet(self):
        return "PACKET [%d %3d] : "\
        "\nT=%.02f Bank %.02f Att %.02f Head %.02f \n"\
         "T=%.02f Acc [%.02f %.02f %.02f] Mag [%.02f %.02f %.02f] Gyr [%.02f %.02f %.02f]" \
            % (self.src, self.seq, \
               self.tfull, self.bank, self.attitude, self.heading, \
               self.traw, \
               self.acc[0], self.acc[1], self.acc[2], \
               self.mag[0], self.mag[1], self.mag[2], \
               self.gyr[0], self.gyr[1], self.gyr[2])

## ##################################################
## ##################################################
        
class IMUStreamParser:
    # Sync bytes
    SYNC = [0xb0, 0x0b, 0x5b, 0x00, 0xb5]
    HEADER_SIZE   = 5
    LENGTH_OFFSET = HEADER_SIZE + 1
    SEQ_SIZE      = 2
    PAYLOAD_AHRS = 22
    PAYLOAD_RAW  = 42
    PAYLOAD_FULL = 58

    PAYLOADS      = [PAYLOAD_AHRS,PAYLOAD_RAW,PAYLOAD_FULL]
    
    def __init__(self, callback):
        # Initialize variables
        self.len = 0
        self.data = []
        self.serial_ok = False
        self.callback = callback
        
    def check_header(self):
        for i in range(0,5):
            if self.data[i] != IMUStreamParser.SYNC[i]:
                return False
        return True
    
    def check_length(self):
        if self.data[IMUStreamParser.HEADER_SIZE] in IMUStreamParser.PAYLOADS:
            self.len = self.data[IMUStreamParser.HEADER_SIZE] + IMUStreamParser.SEQ_SIZE
            return True
        return False
        
    # Original complete one call parse
    def parse(self, data):
        # Parse each byte individually
        self.data = self.data + data
        
        while len(self.data) > 0 and self.data[0] != IMUStreamParser.SYNC[0]:
            self.data.pop()

        if len(self.data) >= (IMUStreamParser.HEADER_SIZE):
            if (not self.check_header()):
                del self.data[0:len(self.data)]
                return
 
        if len(self.data) >= (IMUStreamParser.LENGTH_OFFSET):
             if (not self.check_length()):
                 del self.data[0:len(self.data)]
                 return

        if len(self.data) >= (IMUStreamParser.LENGTH_OFFSET + self.len):
            
            p = IMUStreamPacket()
            p.parse(self.data[IMUStreamParser.LENGTH_OFFSET:self.len + IMUStreamParser.LENGTH_OFFSET], self.len, IMUStreamParser.PAYLOADS)

            if p.ok:
                if self.callback:
                    self.callback(p)
            else:
                pass

            del self.data[0:len(self.data)]




    # Optimized byte reading in two phases
    # First phase : getting number of bytes until the end of the message
    def get_size_to_read(self, header):
        # Parse each byte individually
        self.data = self.data + header
#        copy=[]+self.data
        
#        print('IMUStreamParser.SYNC[0] : ',IMUStreamParser.SYNC[0])
        while len(self.data) > 0 and self.data[0] != IMUStreamParser.SYNC[0]:
            self.data.pop(0)
        if len(self.data) == 0:
#            print("header and data completely popped : data size = ",len(self.data))
#            print('len of data + header before pop : ',len(copy),"  header was :",header)
            return -1 # return to get new bytes
#        print("header and data size = ",len(self.data),"data[0]==",self.data[0])
        
        
        if len(self.data) >= (IMUStreamParser.HEADER_SIZE):
            if (not self.check_header()):
#                del self.data[0:IMUStreamParser.HEADER_SIZE] # Invalid data
                self.data.pop(0)#Most likely a false positive on the first byte IMUStreamParser.SYNC[0]
                print("invalid header check")
                return -1 # return to get new bytes
        else :
#            print("Header too short for header check : ",self.data)
            return -1 # return to get new bytes
        # Complete Header checked
            
            
        if len(self.data) >= (IMUStreamParser.LENGTH_OFFSET):
            if (not self.check_length()):
                del self.data[0:IMUStreamParser.LENGTH_OFFSET] # Invalid data
#                print("invalid length check")
                return -1 # return to get new bytes
        else :
#            print("Header too short for length check",self.data)
            return -1 # return to get new bytes
    
        if len(self.data) >= (IMUStreamParser.LENGTH_OFFSET + self.len):
#            print("Message already available. Should not happen.")
            return 0 # Message already available, procede directly to data processing
        else :#len(self.data) < (IMUStreamParser.LENGTH_OFFSET + self.len)
            # Normal Case, read missing bytes to complete the message before
            # proceding to data processing
            size_left_to_read = ((IMUStreamParser.LENGTH_OFFSET + self.len) - len(self.data))
#            print("size_left_to_read : ",size_left_to_read)
            return size_left_to_read
            
            
            
    # Second phase : Process the completed message
    def data_parse(self, data):
        self.data = self.data + data
#        print("Processing full message of length :",len(self.data))
        if len(self.data) >= (IMUStreamParser.LENGTH_OFFSET + self.len):
            
            p = IMUStreamPacket()
            p.parse(self.data[IMUStreamParser.LENGTH_OFFSET:self.len + IMUStreamParser.LENGTH_OFFSET], self.len, IMUStreamParser.PAYLOADS)

            if p.ok:
                if self.callback:
                    self.callback(p)
            else:
                pass

            del self.data[0:(IMUStreamParser.LENGTH_OFFSET + self.len)]
#            print(len(self.data))
#            del self.data[0:len(self.data)]


## ##################################################
## ##################################################

class IMUStreamStats:
    nodes      = {}
    TIMEOUT    = 2

    def __init__(self):
        self.nodes = {}

    def update(self,id):
        # update sensor stats
        if not id in self.nodes.keys():
            self.nodes[id] = {}
            self.nodes[id]['packets'] = 0
            self.nodes[id]['start_time'] = datetime.datetime.now()
        self.nodes[id]['packets'] = self.nodes[id]['packets'] + 1
        self.nodes[id]['last_time'] = datetime.datetime.now()

    def show_line(self,id):
        BLUE = '\033[94m'
        ENDC = '\033[0m'
        col = BLUE
        pkt = self.nodes[id]['packets']
        pps = float(pkt) / float((datetime.datetime.now() - self.nodes[id]['start_time']).total_seconds())
        sys.stdout.write("%s  node %s : %7d pkts - %02.02f pkt/s  %s\n" %
                         (col,ord(id),pkt,pps,ENDC))

    def show(self):
        CLEAR = '\033[2J\033[H'
        sys.stdout.write(CLEAR)
        sys.stdout.write("\nIMU Stream nodes network stats:\n\n")
        now = datetime.datetime.now()
        for id in sorted(self.nodes):
            if (now - self.nodes[id]['last_time']).total_seconds() < self.TIMEOUT:
                self.show_line(id)
            else:
                del self.nodes[id]

## ##################################################
## ##################################################
