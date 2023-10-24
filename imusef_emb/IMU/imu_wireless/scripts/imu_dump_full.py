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

from IMUStreamLib import IMUStreamLog, IMUStreamParser, IMUStreamPacket, IMUStreamStats

## ##################################################
## ##################################################

parser = OptionParser()
parser.add_option("-p", "--port", help="select the port, default ttyACM0 (serial mode)", type="string", default="/dev/ttyACM0")
parser.add_option("-b", "--baudrate", help="select the baudrate to use, default 500000", type="int", default="500000")
parser.add_option("-o", "--output", help="output data to file", type="string", default="")
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
#out = open('/home/cybathlon/Bureau/Cybathlon/data_files/data_imu.txt', 'w')
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
        if out is not 0:
            out.write('%d \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f \t %f\n' % \
                    (p.src, time.clock(), p.tfull, p.bank, p.attitude, p.heading, \
                     p.traw, p.acc[0], p.acc[1], p.acc[2], p.mag[0], p.mag[1], \
                     p.mag[2], p.gyr[0], p.gyr[1], p.gyr[2]))
            

## ##################################################
## ##################################################

def main():
    # Open serial port
    ser = serial.Serial(options.port, options.baudrate, timeout=0)
    ser.flush()
    
    parser = IMUStreamParser(packet_received)
    log.log_info("Listening on port %s at %d bauds" % (options.port, options.baudrate))
    
    if out is not 0:
        out.write('src \t time \t tahrs \t bank \t attitude \t heading \t' \
        ' traw \t acc[0] \t acc[1] \t acc[2] \t mag[0] \t mag[1] \t mag[2] \t gyr[0] \t gyr[1] \t gyr[2]\n')
    
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
