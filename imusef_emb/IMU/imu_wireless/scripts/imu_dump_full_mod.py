#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# IMU STDMA parser
# Copyright (C) 2015 HIKOB. All rights reserved.
# 
# Created on : Jan 8 2016
# Author : Matthieu Lauzier <matthieu.lauzier.at.hikob.com>
#

#
# This executable allows parsing the Hikob Fox AHRS + Raw data transmitted 
# on a serial port (default /dev/ttyACM0) by a coordinator.
# Options are given underneath.
# The output file format is the following :
# src, tahrs, bank, attitude, heading, traw, acc(*3), mag(*3), gyr(*3)
# Print on standard output is given with option "-d 4"
#

from optparse import OptionParser
import serial 
import sys, traceback
import time
import datetime
import os
import numpy as np

from IMUStreamLib import IMUStreamLog, IMUStreamParser, IMUStreamPacket, IMUStreamStats

import threading


## ##################################################
## ##################################################
dir_path = os.path.dirname(os.path.realpath(__file__))
parser = OptionParser()
parser.add_option("-p", "--port", help="select the port, default ttyACM0 (serial mode)", type="string", default="/dev/IMUFOX")#"/dev/ttyACM0")
parser.add_option("-b", "--baudrate", help="select the baudrate to use, default 128000", type="int", default="115200")

parser.add_option("-o", "--output", help="output data to file", type="string", default=dir_path+"/data/data_imu.txt")
parser.add_option("-d", "--loglevel", help="log level", type="int", default="3")
parser.add_option("-s", "--stats", help="show packets statistics", action='store_true', dest='stats')

options, args = parser.parse_args()

## ##################################################
## ##################################################

log = IMUStreamLog(options.loglevel, True)
if options.output is not '':

    out = open(options.output, "w")
else:
    out = 0

#usleep = lambda x: time.sleep(x/1000000.0)

## ##################################################
## ##################################################

last_show = datetime.datetime.now()
stats = IMUStreamStats()
STATS_REFRESH_DELAY = 0.128
 
global bank
bank = 0
global attitude
attitude = 0
global heading
heading = 0

global READY
READY = 0

global DEBUG
DEBUG = False


#global inc_counter
#inc_counter = 0
   
def packet_received(p):
    global log
    global out
    global options
    global stats
    global last_show
    global STATS_REFRESH_DELAY
    global bank
    global attitude
    global heading
    
    global inc_counter

    if p.src < 1 or p.src > 8:
        return
#    if options.stats:
#        stats.update(chr(p.src))
#        nao = datetime.datetime.now()
#        if float((nao - last_show).total_seconds()) > STATS_REFRESH_DELAY:
#            stats.show()
#            last_show = nao
#    else:
#        log.log_debug(p.print_packet())
    attitude = p.attitude
    bank = p.bank
    heading = p.heading
    
#    inc_counter = inc_counter + 1
    
    
#    if inc_counter > 100 :
#        print("100 samples received")
#        inc_counter = 0
#    print("attitude : ",attitude," bank : ",bank," heading : ",heading)

## ##################################################

def main(e):

    global READY
    global DEBUG

    connected = False
    #    global inc_counter

    while not e.is_set() and not connected:
        try:

            READY = 0

            # Open serial port
            # SET PORT NAME ABOVE IN PARSER OPTIONS
            ser = serial.Serial(options.port, options.baudrate, timeout=2)

            #ser = serial.Serial("/dev/ttyACM0", options.baudrate, timeout=0)
            #ser = serial.Serial("/dev/ttyACM1", options.baudrate, timeout=0)
            ser.flush()
            connected = True

        except Exception as error:

            if DEBUG: print(error)

            READY = -2
            time.sleep(2)

    
    parser = IMUStreamParser(packet_received)
    log.log_info("Listening on port %s at %d bauds" % (options.port, options.baudrate))
    
#    start_time = time.time() # For inc_counter
    while not e.is_set():
        try:
            ## old method for reading with non-blocking serial connection
#            data = ser.read(100) # For non blocking
#            datao = [ord(i) for i in data]
#            if (len(datao) > 0):
#                parser.parse(datao)
            
            ## New method for reading with blocking serial connection
            header = ser.read(6)
            # 1 or 6 for optimized header size (while blocking). 
            # Previously was 100 with non blocking.
            header_o = [ord(i) for i in header]
            if (len(header_o) > 0):
                size_to_read = parser.get_size_to_read(header_o)
                
                if size_to_read >= 0 :
#                    print("size_to_read positive : ",size_to_read)
                    data = ser.read(size_to_read)
                    datao = [ord(i) for i in data]
                    parser.data_parse(datao)
                    READY = 1
                else:
#                    print("size_to_read negative which means get new bytes")
                    pass
            else :
                READY = 0
                #print("WIRELESS IMU : Serial Read Timeout")
            
            #time.sleep(0.001)

        except KeyboardInterrupt:
            log.log_info("Quitting")
            
            ## inc_counter usage : 
            ## outputs a mean duration between two IMU message being processed
#            stop_time = time.time()
#            mean_data_rate = (stop_time - start_time)/inc_counter
#            print("Final inc_counter : ",inc_counter,"Mean data rate : ",mean_data_rate)
            
            break
        except serial.serialutil.SerialException:
            log.log_info("Serial port exception. Quitting")
            break
        except:
            log.log_error("exception: %s" % sys.exc_info()[0])
            traceback.print_exc(file=sys.stdout)
            exit()
   
     ## DEBUG LINES
     ## inc_counter prints on proper exit from manager 
#    log.log_info("Quitting imu_dump_full_mod from above")
#    stop_time = time.time()
#    mean_data_rate = (stop_time - start_time)/inc_counter
#    print("Final inc_counter : ",inc_counter,"Mean data rate : ",mean_data_rate)
   
   
## ##################################################
## ##################################################

if __name__ == "__main__":

    e = threading.Event()
    main(e)

## ##################################################
## ##################################################
