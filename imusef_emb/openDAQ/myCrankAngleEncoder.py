#!/usr/bin/env python
"""
Python module to read the crank angle of the Baumer MDFK08 encoder using an openDAQ module

@author: Martin Schmoll

"""

import os, sys
import time
import threading
from multiprocessing import Process, Value
from opendaq import *


DEBUG = True




class myCrankAngleEncoder(object):

    def __init__(self):


        # Settings
        self.__FLAG_ENCODER_INITIALIZED = False # Informs whether the Encoder has been initialized (based on Z-Channel)
        self.__KILL_PROCESS = Value('i', 0)     # Kills the Process
        self.__port = '/dev/OPENDAQ'            # Port of the openDAQ device
        self.__Encoder_Resolution = 360         # Resolution of the Encoder
        self.__Sleep_acquisition = 0.001        # 1000 Hz

        # Variables
        self.__myOpenDAQ = None             # Variable for the OpenDAQ object
        self.__Timestamp = 0                # [s]
        self.__Counter = 0                  # Current Counter value

        # Output
        self.__Encoder = Value('i', 0)              # 0 - 360
        self.__Encoder_Offset = Value('i', 0)       # 0 - 360, to obtain the absolute Position
        self.__TriggerEncoderInit = Value('i', 0)   # Initiates the Encoder Initialisation

        # State of the Module
        # -2 ... ERROR
        # -1 ... Module not activated
        #  0 ... Module not ready
        #  1 ... Module ready
        self.__Status = Value('i', -1)

    # Configures the openDAQ device and starts a separate Process
    def start(self):

        # Start Process
        self.__read_Process = Process(target=self.__process_run, args=())
        self.__read_Process.daemon = True
        self.__read_Process.start()

    # Initialized the Encoder if neccessary
    def initEncoder(self):
        self.__TriggerEncoderInit.value = 1



    # Reading function executed by the process
    def __process_run(self):

        # Connect openDAQ
        if DEBUG: print("OpenDAQ (CrankAngle): Trying to connect to DAQ")
        try:
            self.__Status.value = 0
            self.__myOpenDAQ = DAQ(self.__port)
            self.__myOpenDAQ.set_led(LedColor.ORANGE)

        except:
            self.__Status.value = -2
            if DEBUG: print("OpenDAQ (CrankAngle): Unable to connect DAQ on Port: " + self.__port)
            return

        if DEBUG: print("OpenDAQ (CrankAngle): Connected to openDAQ")

        ## Setup openDAQ

        # Encoder (DI6/DI5)
        self.__myOpenDAQ.init_encoder(self.__Encoder_Resolution)


        if DEBUG: print("OpenDAQ (CrankAngle): Successfully started!")


        ## Main Loop
        while self.__KILL_PROCESS.value == 0:

            try:
                # Initialize Encoder if neccessary
                if self.__TriggerEncoderInit.value == 1:

                    self.__Encoder_Offset.value = self.__myOpenDAQ.get_encoder()
                    self.__TriggerEncoderInit.value = 0
                    self.__FLAG_ENCODER_INITIALIZED = True
                    self.__Status.value = 1

                # Read Encoder
                if self.__FLAG_ENCODER_INITIALIZED:

                    temp_val = self.__myOpenDAQ.get_encoder() - self.__Encoder_Offset.value

                    if (temp_val<0):
                        temp_val += self.__Encoder_Resolution

                    self.__Encoder.value = temp_val
                else:
                    # Encoder not ready
                    self.__Encoder.value = -1

                time.sleep(self.__Sleep_acquisition)
            except Exception as error:
                if DEBUG: print("OpenDAQ (CrankAngle):" + str(error))
                break

        self.__clean_exit()

    # Returns the current State of the module
    def getStatus(self):
        return self.__Status.value

    # Returns the current value of the Encoder
    def getEncoderValue(self):
        return self.__Encoder.value


    # Stops the process and performs a clean exit
    def stop(self):
        self.__Status.value = -1
        self.__KILL_PROCESS.value = 1;
        time.sleep(1)
        self.__read_Process.terminate()


    # Complete exit sequence in a 'one call' function
    def __clean_exit(self):

        self.__myOpenDAQ.stop_encoder()

        self.__myOpenDAQ.stop()
        self.__myOpenDAQ.flush()
        self.__myOpenDAQ.close()

        if DEBUG: print("OpenDAQ (CrankAngle): Clean Exit performed!")

