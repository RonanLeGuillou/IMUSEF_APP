#!/usr/bin/env python
"""
Python module to read data from the Hometrainer via the openDAQ device

TODO: Put logfile writing into a different thread

@author: Ronan LE GUILLOU & Martin Schmoll

"""

import os, sys
import time
import threading
from UDP.UDP_Server import  UDP_Server
from IMUSEF_Data import  IMUSEF_Data
from multiprocessing import Process, Value
from opendaq import *


DEBUG = True




class myDAQManager(object):


    def __init__(self):

        # Constants

        # Settings
        self.__KILL_PROCESS = Value('i', 0)     # Kills the Process
        self.__port = '/dev/OPENDAQ'            # Port of the openDAQ device
        self.__Sleep_acquisition = 0.001        # 1000 Hz

        # Calibration Values
        self.__Voltage0 = 1.22056               # [V]   TODO: To be verified
        self.__Pos0     = 131.5                 # [deg]
        self.__Voltage1 = -3.17982              # [V]   TODO: To be verified
        self.__Pos1     = 284.9                 # [deg]
        self.__ScaleFactor_Speed = 0.0098       # [V] per [deg/sec]


        # Variables
        self.__myOpenDAQ = None                 # Variable for the OpenDAQ object
        self.__AnalogInput = 0.0                # [V] - Biodex Positon
        self.__AnalogInput2 = 0.0               # [V] - Biodex Speed

        # Output
        self.__Position = Value('d', 0.0)       # [deg]
        self.__Speed = Value('d', 0.0)          # [deg/s]

        # State of the Module
        # -2 ... ERROR
        # -1 ... Module not activated
        #  0 ... Module not ready
        #  1 ... Module ready
        self.__State = Value('i', -1)






    # Configures the openDAQ device and starts a separate Process
    def start(self):

        # Start Process
        self.__read_Process = Process(target=self.__process_run, args=())
        self.__read_Process.daemon = True
        self.__read_Process.start()


    # Reading function executed by the process
    def __process_run(self):

        # Connect openDAQ
        if DEBUG: print("myDAQManager: Trying to connect to openDAQ")
        try:
            self.__State.value = 0
            self.__myOpenDAQ = DAQ(self.__port)
            self.__myOpenDAQ.set_led(LedColor.ORANGE)

        except:
            self.__State.value = -2
            if DEBUG: print("myDAQManager: Unable to connect DAQ on Port: " + self.__port)
            return

        if DEBUG: print("myDAQManager: Connected to openDAQ")

        ## Setup openDAQ

        # Analog Input (A8)
        self.__myOpenDAQ.conf_adc(pinput=8, ninput=0, gain=Gains.S.x1, nsamples=1)
        self.__myOpenDAQ.conf_adc(pinput=7, ninput=0, gain=Gains.S.x1, nsamples=1)
        #self.__myOpenDAQ.conf_adc(8)

        if DEBUG: print("myDAQManager: Successfully started!")
        self.__State.value = 1

        ## Main Loop
        while self.__KILL_PROCESS.value == 0:

            try:

                # Read and Filter Analog value

                #self.__AnalogInput = self.__myOpenDAQ.read_analog()
                read = self.__myOpenDAQ.read_all()
                self.__AnalogInput = read[7]
                self.__AnalogInput2 = read[6]

                # self.__AnalogInput_Filter.append(self.__myOpenDAQ.read_analog())
                # self.__AnalogInput_Filter.pop(0)
                # self.__AnalogInput = sum(self.__AnalogInput_Filter) / len(self.__AnalogInput_Filter)

                self.__process_data()

                time.sleep(self.__Sleep_acquisition)
            except Exception as error:
                if DEBUG: print("OPENDAQ: ERROR:" + str(error))
                break

        self.__clean_exit()




    # Calculates the real values for Torque, Speed and Power
    def __process_data(self):

        # Calculation of position
        relativeVoltage = (self.__AnalogInput - self.__Voltage0)/(self.__Voltage1 - self.__Voltage0)

        self.__Position.value = relativeVoltage *(self.__Pos1 - self.__Pos0) + self.__Pos0

        # Calculate Speed
        self.__Speed.value = self.__AnalogInput2 / self.__ScaleFactor_Speed


    # Returns the current Position of the Biodex
    def getPosition(self):
        return self.__Position.value

    # Returns the current Speed of the Biodex
    def getSpeed(self):
        return self.__Speed.value

    # Returns the current State of the module
    def getState(self):
        return self.__State.value

    # Stops the process and performs a clean exit
    def stop(self):
        self.__State.value = -1
        self.__KILL_PROCESS.value = 1;
        time.sleep(1)
        self.__read_Process.terminate()


    # Complete exit sequence in a 'one call' function
    def __clean_exit(self):


        self.__myOpenDAQ.stop()
        self.__myOpenDAQ.flush()
        self.__myOpenDAQ.close()

        if DEBUG: print("myDAQManager: Clean Exit performed!")





# PROGRAM for testing
if __name__ == '__main__':

    e = threading.Event()

    myUDPServer = UDP_Server(12345)
    myUDPServer.start(e)

    data = IMUSEF_Data()

    print("Main side : Creating instance of HOMETRAINER")

    myDAQ = myDAQManager()
    myDAQ.start()

    time.sleep(0.5)

    try:
        while True :

            # Only print data if module is ready
            if myDAQ.getState()==1:

                data.timestamp = time.time()

                sys.stdout.write('\r Position:' + str(myDAQ.getPosition()))
                sys.stdout.flush()  # important

            time.sleep(0.01)


    except KeyboardInterrupt:
        print("KeyboardInterrupt during MAIN STIM LOOP of user interface")
        myDAQ.stop()

    except Exception as e:
        print("Exception during MAIN STIM LOOP of user interface")
        myDAQ.stop()






