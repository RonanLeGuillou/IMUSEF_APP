#!/usr/bin/env python
"""
Python module to read data from the Hometrainer via the openDAQ device

TODO: Put logfile writing into a different thread

@author: Ronan LE GUILLOU & Martin Schmoll

"""

import os, sys
import time
import threading
from Hometrainer_Data import Hometrainer_Data
from UDP.UDP_Server import  UDP_Server
from IMUSEF_Data import  IMUSEF_Data
from multiprocessing import Process, Value
from opendaq import *


DEBUG = True




class HOMETRAINER(object):


    def __init__(self):

        # Constants
        self.__k_Torque = -1599.48;     # Conversion slope in [mV/Nm]; Attention: Negative coefficient because the sensor is mounted inverted compared to the documentation
        self.__HT_diam = 0.05           # Diameter of hometrainer barrel in [m]
        self.__PI = 3.14159265          # The most undelicious cake

        # Settings
        self.__FLAG_LOG_DATA = False            # Saves all measured data into a logfile
        self.__FLAG_ACTIVATE_ENCODER = True     # Allows the encoder to be read
        self.__FLAG_ENCODER_INITIALIZED = False # Informs whether the Encoder has been initialized (based on Z-Channel)
        self.__KILL_PROCESS = Value('i', 0)     # Kills the Process
        self.__port = '/dev/OPENDAQ2'           # Port of the openDAQ device
        self.__Encoder_Resolution = 360         # Resolution of the Encoder
        self.__Sleep_acquisition = 0.001        # 1000 Hz
        self.__FileName = None                  # Desired Name for LogFile


        # Variables
        self.__myOpenDAQ = None             # Variable for the OpenDAQ object
        self.__Timestamp = 0                # [s]
        self.__HT_RPM = 0.00                # Rotational Speed of the Hometrainer
        self.__Counter = 0                  # Current Counter value
        self.__AnalogInput = 0.0            # [V]
        self.__AnalogInput_Offset = 0.0     # Offset of the input signal
        self.__LogFile = None               # Logfile
        self.__isCalibrated = Value('i', 0)         # Defines wheter the system needs to be calibrated

        # Filters
        self.__RPM_Filter = []
        self.__RPM_Filter_Size = 30

        self.__AnalogInput_Filter = []
        self.__AnalogInput_Filter_Size = 30

        # Averaging Lists
        self.__Power_List = []
        self.__Power_List_Size = 100

        # Output
        self.__data = Hometrainer_Data();           # Collection of Data
        self.__Torque = Value('d', 0.0)             # [Nm]
        self.__Power = Value('d', 0.0)              # [W]
        self.__Power_AVG = Value('d', 0.0)          # [W]
        self.__Speed = Value('d', 0.0)              # [km/h]
        self.__Distance = Value('d', 0.0)           # [m]
        self.__Encoder = Value('i', 0)              # 0 - 360
        self.__Encoder_Offset = Value('i', 0)       # 0 - 360, to obtain the absolute Position
        self.__TriggerEncoderInit = Value('i', 0)   # Initiates the Encoder Initialisation

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


    # Sets up a new LogFile
    def __setupLogFile(self):

        ## If no log file name given :
        ## Find an unused file name by incrementing the Trialx file index
        self.__Path_Logfile = self.__FileName

        if self.__Path_Logfile == None:

            file_id='hometrainer_data'
            file_ext='.txt'
            file_number=1
            self.__Path_Logfile= '%s%s%d%s' % ("Data/",file_id, file_number, file_ext)

            while os.path.isfile(self.__Path_Logfile):
                file_number=file_number+1
                self.__Path_Logfile= '%s%s%d%s' % ("Data/",file_id, file_number, file_ext)

        self.__LogFile=open(self.__Path_Logfile, 'a+')

        if DEBUG: print('Hometrainer : Name of LogFile is: ', self.__Path_Logfile)

        self.__LogFile.write('Time(s) \t'
                            ' Counter \t'
                            ' Encoder \t'
                            ' AnalogInput \t'
                            ' Torque \t'
                            ' HT_Rpm \t'
                            ' Power \t'
                            ' Speed \n')

        self.__FLAG_LOG_DATA = False


    # Writes the current data to file
    def __write2File(self):

        str_data_output =   '%.6f' % self.__Timestamp + '\t'
        str_data_output += str(self.__Counter) + '\t '
        str_data_output += str(self.__Encoder.value) + '\t '
        str_data_output += str(self.__AnalogInput) + '\t '
        str_data_output += str(self.__Torque.value) + '\t '
        str_data_output += str(self.__HT_RPM) + '\t '
        str_data_output += str(self.__Power.value) + '\t '
        str_data_output += str(self.__Speed.value) + '\n '

        self.__LogFile.write(str_data_output)


    # Triggers a calibration of the running system
    def calibrate(self):
        self.__isCalibrated.value = 0

    # Initialized the Encoder if neccessary
    def initEncoder(self):
        self.__TriggerEncoderInit.value = 1


    # Perform calibration from external
    def reCalibrate(self):
        self.__isCalibrated.value = 0

    # Calibrates the System
    def __calibrate(self):

        self.__State.value = 0

        # Get AnalogInput_Offset
        for i in range(100):
            self.__AnalogInput_Filter.append(self.__myOpenDAQ.read_analog())
            time.sleep(self.__Sleep_acquisition)

        self.__AnalogInput_Offset = sum(self.__AnalogInput_Filter) / len(self.__AnalogInput_Filter)

        self.__AnalogInput_Filter = [self.__AnalogInput_Offset] * self.__AnalogInput_Filter_Size

        # Get the Starting TimeStamp
        self.__Timestamp = time.time()

        # Reset Counter
        self.__Counter = self.__myOpenDAQ.get_counter(reset=True)

        # Sleep
        time.sleep(self.__Sleep_acquisition)

        # Ready to rumble
        self.__isCalibrated.value = 1
        self.__myOpenDAQ.set_led(LedColor.GREEN)
        self.__State.value = 1

        if DEBUG: print("HOMETRAINER: Successfully calibrated!")


    # Reading function executed by the process
    def __process_run(self):

        # Connect openDAQ
        if DEBUG: print("HOMETRAINER: Trying to connect to openDAQ")
        try:
            self.__State.value = 0
            self.__myOpenDAQ = DAQ(self.__port)
            self.__myOpenDAQ.set_led(LedColor.ORANGE)

        except:
            self.__State.value = -2
            if DEBUG: print("HOMETRAINER: Unable to connect DAQ on Port: " + self.__port)
            return

        if DEBUG: print("HOMETRAINER: Connected to openDAQ")

        ## Setup openDAQ

        # Encoder (DI6/DI5)
        if self.__FLAG_ACTIVATE_ENCODER:
            self.__myOpenDAQ.init_encoder(self.__Encoder_Resolution)

        # Analog Input (A8)
        self.__myOpenDAQ.conf_adc(pinput=8, ninput=0, gain=Gains.S.x1, nsamples=1)

        # Counter (DI5)
        self.__myOpenDAQ.init_counter(edge=True)
        self.__myOpenDAQ.get_counter(reset=True)

        # Create LogFile
        if self.__FLAG_LOG_DATA:
            self.__setupLogFile()

        if DEBUG: print("HOMETRAINER: Successfully started!")


        ## Main Loop
        while self.__KILL_PROCESS.value == 0:

            try:
                # Initialize Encoder if neccessary
                if (self.__FLAG_ACTIVATE_ENCODER and \
                    self.__TriggerEncoderInit.value == 1):

                    self.__Encoder_Offset.value = self.__myOpenDAQ.get_encoder()
                    self.__TriggerEncoderInit.value = 0
                    self.__FLAG_ENCODER_INITIALIZED = True

                # Calibrate system if requested
                if self.__isCalibrated.value == 0:
                    self.__calibrate()


                # Update Timestamp
                new_Timestamp = time.time()
                delta_t = new_Timestamp - self.__Timestamp
                self.__Timestamp = new_Timestamp

                # Read and Filter Analog value
                self.__AnalogInput_Filter.append(self.__myOpenDAQ.read_analog())
                self.__AnalogInput_Filter.pop(0)
                self.__AnalogInput = sum(self.__AnalogInput_Filter) / len(self.__AnalogInput_Filter)


                # Read and Reset Counter
                self.__Counter = self.__myOpenDAQ.get_counter(reset=True)


                # Read Encoder
                if self.__FLAG_ACTIVATE_ENCODER and self.__FLAG_ENCODER_INITIALIZED:

                    temp_val = self.__myOpenDAQ.get_encoder() - self.__Encoder_Offset.value

                    if (temp_val<0):
                        temp_val += self.__Encoder_Resolution

                    self.__Encoder.value = temp_val
                else:
                    # Encoder not ready
                    self.__Encoder.value = -1

                # Calculate the real values
                self.__process_data(delta_t)

                # Write Data to File
                if self.__FLAG_LOG_DATA:
                    self.__write2File()

                time.sleep(self.__Sleep_acquisition)
            except Exception as error:
                if DEBUG: print("HOMETRAINER: ERROR:" + str(error))
                break

        self.__clean_exit()




    # Calculates the real values for Torque, Speed and Power
    def __process_data(self, delta_t):

        ## Calculation Torque from AnalogInput Value
        # Torque [Nm] = (AnalogInput [mV] -  AnalogInput_Offset [mV]) / Conversion_coefficient [mV/Nm]
        self.__Torque.value = ((self.__AnalogInput - self.__AnalogInput_Offset) * 1000.0) / self.__k_Torque

        ## Calculate cycled distance
        diff_distance = self.__PI*self.__HT_diam * (self.__Counter / 360.0)
        self.__Distance.value = self.__Distance.value + diff_distance

        ## Calculation rotaional Speed of the Hometrainer Barrel
        # Rotations per minute = (CounterValue  / 360) / time_elapsed [min]
        RPM = (self.__Counter/360.0) / (delta_t/60.0)

        # Filtering
        if len(self.__RPM_Filter) < self.__RPM_Filter_Size:
            self.__RPM_Filter.append(RPM)
            self.__HT_RPM = 0.0
        else:
            self.__RPM_Filter.append(RPM)
            self.__RPM_Filter.pop(0)
            self.__HT_RPM = sum(self.__RPM_Filter) / len(self.__RPM_Filter)


        ## Power from actual Torque measured and rotaional speed
        # Power [W] = Torque [Nm] * Cadence [rad/s]
        self.__Power.value = self.__Torque.value * 2.0 * self.__PI * self.__HT_RPM / 60.0

        # Average Power
        if len(self.__Power_List) < self.__Power_List_Size:
            self.__Power_List.append(self.__Power.value)
            #self.__Power_AVG.value = 0.0
        else:
            self.__Power_List.append(self.__Power.value)
            self.__Power_AVG.value = sum(self.__Power_List) / len(self.__Power_List)
            self.__Power_List = []


        ## Speed Calculation
        # Speed [km/h] = Rotations per hour * Circumference [km]
        self.__Speed.value = (self.__HT_RPM * 60.0) * (self.__HT_diam * self.__PI / 1000.0)



    # Returns the current State of the module
    def getState(self):
        return self.__State.value

    # Returns the current Torque
    def getTorque(self):
        return self.__Torque.value

    # Returne the current Power
    def getPower(self):
        return self.__Power.value

    # Returns the current Speed
    def getSpeed(self):
        return self.__Speed.value

    # Returns the current Distance cycled
    def getDistance(self):
        return self.__Distance.value


    # Returns the current value of the Encoder
    def getEncoderValue(self):
        return self.__Encoder.value


    # Returns the current Data as a Hometrainer_Data Object
    def getData(self):

        #self.__data.Hometrainer_timestamp = self.__Timestamp
        #self.__data.counter_value = self.__Counter
        self.__data.encoder_value = self.__Encoder.value
        #self.__data.analog_value =self.__AnalogInput
        self.__data.Torque = self.__Torque.value
        #self.__data.HT_Rpm = self.__HT_RPM
        #self.__data.RW_Rpm = self.RW_Rpm
        self.__data.Power = self.__Power.value
        self.__data.Power_AVG = self.__Power_AVG.value
        self.__data.Speed = self.__Speed.value
        self.__data.Distance = self.__Distance.value

        
        return self.__data



    # Stops the process and performs a clean exit
    def stop(self):
        self.__State.value = -1
        self.__KILL_PROCESS.value = 1;
        time.sleep(1)
        self.__read_Process.terminate()


    # Complete exit sequence in a 'one call' function
    def __clean_exit(self):

        if self.__FLAG_ACTIVATE_ENCODER:
            self.__myOpenDAQ.stop_encoder()

        self.__myOpenDAQ.stop()
        self.__myOpenDAQ.flush()
        self.__myOpenDAQ.close()

        if self.__FLAG_LOG_DATA :
            self.__LogFile.close()

        if DEBUG: print("HOMETRAINER: Clean Exit performed!")





# PROGRAM for testing
if __name__ == '__main__':

    e = threading.Event()

    myUDPServer = UDP_Server(12345)
    myUDPServer.start(e)

    data = IMUSEF_Data()

    print("Main side : Creating instance of HOMETRAINER")

    HT = HOMETRAINER()
    HT.start()

    time.sleep(0.5)

    try:
        while True :

            # Only print data if module is ready
            if HT.getState()==1:

                data.timestamp = time.time()
                data.Hometrainer_DATA = HT.getData()
                myUDPServer.sendData(data.getJSON())

                sys.stdout.write('\r Torque:' + str(HT.getTorque()) + "\t Power: " + str(HT.getPower()) + "\t Speed: " + str(HT.getSpeed()) + "\t Encoder: " + str(HT.getEncoderValue()) )
                sys.stdout.flush()  # important

            time.sleep(0.01)


    except KeyboardInterrupt:
        print("KeyboardInterrupt during MAIN STIM LOOP of user interface")
        HT.stop()

    except Exception as e:
        print("Exception during MAIN STIM LOOP of user interface")
        HT.stop()






