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
import numpy as np

global data_2_imus

data_2_imus = np.zeros((2,11))
update_1 = False
update_2 = False

from IMUStreamLib import IMUStreamLog, IMUStreamParser, IMUStreamPacket, IMUStreamStats

## ##################################################
## ##################################################

parser = OptionParser()
parser.add_option("-p", "--port", help="select the port, default ttyACM0 (serial mode)", type="string", default="/dev/ttyACM0")
parser.add_option("-b", "--baudrate", help="select the baudrate to use, default 128000", type="int", default="128000")
parser.add_option("-o", "--output", help="output data to file", type="string", default="/home/camin/Bureau/fwheels/fwheels/bike_and_HR/data_files/data_imu.txt")
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

usleep = lambda x: time.sleep(x/1000000.0)

## ##################################################
## ##################################################

last_show = datetime.datetime.now()
stats = IMUStreamStats()
STATS_REFRESH_DELAY = 0.128
    
def packet_received(p):
    global log
    global out
    global options
    global stats
    global last_show
    global STATS_REFRESH_DELAY
    global update_1
    global update_2
    if p.src < 1 or p.src > 8:
        return
    if options.stats:
        stats.update(chr(p.src))
        nao = datetime.datetime.now()
        if float((nao - last_show).total_seconds()) > STATS_REFRESH_DELAY:
            stats.show()
            last_show = nao
    else:
        log.log_debug(p.print_packet())
        if p.src == 1:
            data_2_imus[0,0] = 1
            data_2_imus[0,1] = p.tfull
            data_2_imus[0,2] = p.bank
            data_2_imus[0,3] = p.attitude
            data_2_imus[0,4] = p.heading
            data_2_imus[0,5] = p.acc[0]
            data_2_imus[0,6] = p.acc[1]
            data_2_imus[0,7] = p.acc[2]
            data_2_imus[0,8] = p.gyr[0]
            data_2_imus[0,9] = p.gyr[1]
            data_2_imus[0,10] = p.gyr[2]
#            update_1 = True
        elif p.src == 2:
            data_2_imus[1,0] = 2
            data_2_imus[1,1] = p.tfull
            data_2_imus[1,2] = p.bank
            data_2_imus[1,3] = p.attitude
            data_2_imus[1,4] = p.heading
            data_2_imus[1,5] = p.acc[0]
            data_2_imus[1,6] = p.acc[1]
            data_2_imus[1,7] = p.acc[2]
            data_2_imus[1,8] = p.gyr[0]
            data_2_imus[1,9] = p.gyr[1]
            data_2_imus[1,10] = p.gyr[2]
#            update_2 = True
     
#        print(' 1: '+str(update_1) + ' 2: '+str(update_2) + '\t\t'+str(time.clock())+'s')    

        out.seek(0,0)
        out.write('%d \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f\n%d \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f\n' % \
                (data_2_imus[0,0],data_2_imus[0,1],data_2_imus[0,2],data_2_imus[0,3],data_2_imus[0,4], data_2_imus[0,5], data_2_imus[0,6], data_2_imus[0,7], data_2_imus[0,8], data_2_imus[0,9], data_2_imus[0,10],\
                data_2_imus[1,0],data_2_imus[1,1],data_2_imus[1,2],data_2_imus[1,3],data_2_imus[1,4],  data_2_imus[1,5], data_2_imus[1,6], data_2_imus[1,7], data_2_imus[1,8], data_2_imus[1,9], data_2_imus[1,10]))
#        update_1 = False
#        update_2 = False

## ##################################################

def main():
    # Open serial port
    ser = serial.Serial(options.port, options.baudrate, timeout=0)
    ser.flush()
    
    parser = IMUStreamParser(packet_received)
    log.log_info("Listening on port %s at %d bauds" % (options.port, options.baudrate))
    
#    if out is not 0:
#       out.write('src \t tahrs \t bank \t attitude \t heading \t' \
#        ' traw \t acc[0] \t acc[1] \t acc[2] \t mag[0] \t mag[1] \t mag[2] \t gyr[0] \t gyr[1] \t gyr[2]\n')
##    
    while True:
        try:
            data = ser.read(100)
            datao = [ord(i) for i in data]
            if (len(datao) > 0):
                parser.parse(datao)
        except KeyboardInterrupt:
            log.log_info("Quitting")
            break
        except serial.serialutil.SerialException:
            log.log_info("Serial port exception. Quitting")
            break
        except:
            log.log_error("exception: %s" % sys.exc_info()[0])
            traceback.print_exc(file=sys.stdout)
            exit()

## ##################################################
## ##################################################

if __name__ == "__main__":
    main()

## ##################################################
## ##################################################
