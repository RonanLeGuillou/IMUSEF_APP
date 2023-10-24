#!/usr/bin/env python
"""
API_HasoStim   -- use wire-connected to a Hasomed Rehastim version 1 Electrical Stimulator

@author: Ronan LE GUILLOU 

@date: October 2018

@credit : Part of the communication functions and protocol are based on the following project
@ https://github.com/PedroLopes/muscle-plotter

"""
#python imports
from __future__ import print_function
import numpy as np
# import bluetooth 
# import socket
import serial
import os
#, syspy
import time
import threading

#imports from this project
# from interface.SerialThingy import SerialThingy
# import interface.singlepulse as singlepulse
#from singlepulse import *
import messages_support
## If version is python3 set corresponding flag to True for later tests
#Python3 = False
#if sys.version_info[0] == 3:
Python3 = True


"""*
	*
	* WARNING XXXXXXXXXXXXXXXXXXXX
	*
	*"""

class HASOSTIM(object):

############	Start of __init__ HASOSTIM 	##########

	def __init__(self):

		self.ACTIVATE_READ = False
		self.DEBUG = False

		self.flag_read = False
		self.ser = None
		self.reading_thread = threading.Thread(target=self.read_from_serial)

		## Byte of channels as bits in a string format
		self.channels_used_as_string = '00000000'



	def read_from_serial(self):
		
		# if self.DEBUG:
		# 	print("Started a listening SerialThread on " + str(self.ser))
		
		while self.flag_read:
			v = self.ser.read(size=1)
			# print(len(v))			
		
			if(len(v) > 0):
				# v = v.decode("utf-8").rstrip('\r\n')
				# not sure if needed for EMS SERIAL RESPONSE
				if self.DEBUG:
					print("SERIAL_THREAD_RESPONSE:" + str(v))					


	def start_reading_thread(self):
		self.reading_thread.start()


## Mutator and accessor for READ FLAG enabling or disabling communication stream reading
	def set_read_flag(self,state = True):
		self.flag_read = state

	def get_read_flag(self):
		return self.flag_read



	def open_port(self, port = None):

		self.ser = serial.Serial(port,
			baudrate=115200,
			bytesize=serial.EIGHTBITS,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_TWO,
			#rtscts=True,
			timeout=1)

		if not self.ser :
			print("Retrying to connect.")
			time.sleep(1)
			self.ser = serial.Serial(port,
				baudrate=115200,
				bytesize=serial.EIGHTBITS,
				parity=serial.PARITY_NONE,
				stopbits=serial.STOPBITS_TWO,
				#rtscts=True,
				timeout=1)

		if not self.ser :
			sys.exit("ERROR : serial module did not manage to connect to \
                      HASOMED Rehastim 1 Stimulator through any COM_port") 



	# def set_intensity_in_mA_on_1_channel(self, chan=1,pw=300,amp=25):
	def send_pulse_in_mA_on_1_channel(self, chan=2,pw=300,amp=25):
		# self.ser.write(msg)
		msg=messages_support.generate_single_pulse(chan, pw, amp)
		self.ser.write(msg)
		# writes the EMS serial message to the console / stdout
		# print(msg)

## This terminate the connection with the stimulator.
## To start communicating with it again you will have to unplug and replug the device to the computer
	def terminate_connection(self):
		msg = messages_support.generate_terminate_connection()
		self.ser.write(msg)
		print('terminate_connection command sent')

## Complete initialization sequence in a 'one call' function
## Can be called with another port than the normal one if you know what your are doing. It might not work.
	def init_connect(self, port = 10):
		print('\ninit_connect : Trying to connect to HASOSTIM\n')
		self.open_port(port)
		print('init_connect : Connected to HASOSTIM\n')
			
		self.set_read_flag()
		self.start_reading_thread()
		

## Stimlation parameters setup
# def generate_channel_list_mode_init(_N_factor,_channels_stim,_channels_lf,_group_time,_main_time):
## _N_factor = Number of stimulation delay in pulses, 0 to 7, used if channel specified both
## as ON with channels_stim AND as Low frequency with channels_lf
## _channels_stim = Channels used : '00001100' for channels 3 and 4 for example
## _channels_lf = Low frequency : '00001100' for low freqency on channels 3 and 4 for example
## _group_time = inter pulse duration in ms for burst mode stimulation
## _main_time = Main time period of stimulation as in inverse of frequency
	def stimulation_param_setup(self, _N_factor,_channels_stim,_channels_lf,_group_time,_main_time):
		
		msg=messages_support.generate_channel_list_mode_init2(_N_factor,
		 _channels_stim, _channels_lf, _group_time,_main_time)
		self.ser.write(msg)


## For each channel used, in lists, in increasing order with respect to the channel number
## _Mode_list	 	2 bits		0..2 single pusle = 0, doublet = 1, triplet = 2)
## _pulse_width_list 	9 bits		0,10..500     10 by 10  pulse width in uS
## _pulse_current_list 	7 bits		0..127   current in mA
## Exemple :
## using channels 3,4 and 6
## _Mode_list = [0,0,0]
## _pulse_width_list = [300,400,600]
## _pulse_current_list = [30,40,60] channel 6 being set to 60 mA with PW = 600 uS

	def send_channel_list_mode_update(self,_Mode_list,_pulse_width_list,_pulse_current_list):

		msg=messages_support.generate_channel_list_mode_update(_Mode_list,
		 _pulse_width_list, _pulse_current_list)
		self.ser.write(msg)


	def send_channel_list_mode_stop(self):
		msg=messages_support.generate_channel_list_mode_stop()
		self.ser.write(msg)


## Complete exit sequence in a 'one call' function
	def clean_exit(self):
		time.sleep(0.010)
		self.terminate_connection();
		time.sleep(0.010)
		self.set_read_flag(False)
		# self.disconnect()



##############################################################
##############################################################
############		MAIN PROGRAM for testing		##########
##############################################################
##############################################################

if __name__ == '__main__':

	print("Main side : Creating instance of HASOSTIM")
	HASO = HASOSTIM()
	HASO.init_connect(port=9)


	# try:
	# 	while True :
	# 		time.sleep(0.1)
	# 		print("Sending pulse")
	# 		HASO.send_pulse_in_mA_on_1_channel(chan=4,pw=300,amp=25)

	# except KeyboardInterrupt:
	# 	print("KeyboardInterrupt during MAIN STIM LOOP of user interface")
	# 	HASO.clean_exit()

	# except Exception as e:
	# 	print("Exception during MAIN STIM LOOP of user interface")
	# 	HASO.clean_exit()
	# 	raise e



	HASO.channels_used_as_string = '00000100' ## Channel 4 ON
	HASO.channels_used_as_string = '00001000' ## Channel 4 ON
	no_low_freqs = '00000000'
	frequency = 10
	period = int(1000/frequency)
	HASO.stimulation_param_setup(0,HASO.channels_used_as_string,no_low_freqs,0,period)
	mode_list = [0]
	pw_list = [200]
	intensity_list = [0]

	intensity_in_mA = 0
	try:
		while True :
			time.sleep(3)
			print("switching stim")
			if intensity_in_mA == 0 :
				intensity_in_mA = 20
			else :
				intensity_in_mA = 0
			print(intensity_in_mA)
			# intensity_list[0] = intensity_in_mA
			HASO.send_channel_list_mode_update([0],[200],[intensity_in_mA])
			# HASO.send_channel_list_mode_update(mode_list,pw_list,intensity_list)

	except KeyboardInterrupt:
		print("KeyboardInterrupt during MAIN STIM LOOP of user interface")
		HASO.send_channel_list_mode_stop()
		HASO.clean_exit()

	except Exception as e:
		print("Exception during MAIN STIM LOOP of user interface")
		HASO.send_channel_list_mode_stop()
		HASO.clean_exit()
		raise e