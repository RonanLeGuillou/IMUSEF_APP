# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 11:33:00 2017

@author: pi
"""


import smbus
 

def init_i2c_bus(bus_conf = 1):
    bus = smbus.SMBus(bus_conf)   
    return bus

def sw_channel(bus, address=0x70,channel=0):  # values 0-3 indicate the channel, anything else (eg -1) turns off all channels
        
#        if   (channel==0): action = 0x04
#        elif (channel==1): action = 0x05
#        elif (channel==2): action = 0x06
#        elif (channel==3): action = 0x07
#        elif (channel==4): action = 0x08
#        else : action = 0x00

        if   (channel==1): action = 0x01
        elif (channel==2): action = 0x02
        elif (channel==3): action = 0x04
        elif (channel==4): action = 0x08
        
        bus.write_byte_data(address,0x04,action)  #0x04 is the register for switching channels 

    

   