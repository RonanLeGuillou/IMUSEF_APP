from IMU.imu_wired.IMU_Data_wired import IMU_Data_wired
from IMUSEF_Data import IMUSEF_Data
from threading import *
import os
import time
import re
from queue import Queue

class DataLogger(object):

    ###################################################################################
    # Constructor
    ###################################################################################
    def __init__(self, directory ="", filename ="", extension = "txt", timestamp = 0):

        # Data Queue
        self.dataQueue = Queue()
        self.Status = -1
        self.TimeStamp_start = None


        ## Setup new File
        if extension == '':
            extension = "txt"

        if directory == '':
            directory = "Data/"
        else:
            directory = "Data/" + directory + "/"

        if filename == "":
            filename = "Datafile"

        # Create a new directory for each day
        if not os.path.exists(directory):
            os.mkdir(directory)

        # Check how many elements there are in the directory
        n =  len(os.listdir(directory+'/')) + 1

        filename = '{:04d}'.format(n) + "_" + filename

        # Create a new Filename
        file_number_str = ""
        file_number = 2

        while os.path.isfile(directory + filename + file_number_str + "." + extension):
            file_number_str = "_" + str(file_number)
            file_number = file_number + 1

        self.file_path = directory + filename + file_number_str + "." +extension

        # Open Datafile
        self.datafile = open(self.file_path, "w")



        # Define Header
        # Log all data even if the modules are not selected
        self.datafile.write(
                            # Timestap
                            'Time[s] \t'
                            
                            # Inputs
                            'Crank_angle_wired[deg] \t'
                            'Crank_angle_wireless[deg] \t'
                            'Thigh_angle_left[deg] \t'
                            'Thigh_angle_right[deg] \t'
                            'Knee_angle_left[deg] \t'
                            'Knee_angle_right[deg] \t'
                            
                            # Cycling Computer Data
                            'Speed[km/h] \t'
                            'Distance[m] \t'
                            'Cadence[RPM] \t'
                            
                            # Powermeter Data
                            'Powermeter_Torque_left[Nm] \t'
                            'Powermeter_Torque_right[Nm] \t'
                            'Powermeter_Torque_total[Nm] \t'
                            'Powermeter_CrankAngle[deg] \t'
                            'Powermeter_Cadence[RPM] \t'
                            'Powermeter_Power[W] \t'
                            
                            # Instrumented Hometrainer Data
                            'Speed_Hometrainer[km/h] \t'
                            'Distance_Hometrainer[m] \t'
                            'Torque_Hometrainer[Nm] \t'
                            'Power_Hometrainer[W] \t'
                            'Power_average_Hometrainer[W] \t'
                            
                            # Physiological Data
                            'Heart_rate[BPM] \t'
                            
                            # Stimulation Data
                            'Stim_Intensity[%] \t'
                            
                            # Buttons
                            'Button_left[bool] \t'
                            'Button_right[bool] \t'
                            'Button_BOOST[bool] \t'
                            'Button_Emergency[bool] \t'

                            # Processed Angle Data
                            'Normalized_thigh_angle_left[%] \t'
                            'Normalized_thigh_angle_right[%] \t'
                            'Normalized_knee_angle_left[%] \t'
                            'Normalized_knee_angle_right[%] \t'
                            'Observer_phase[%] \t'

                            # Controller Data
                            'Remote_controller_ch_active \t'
                            'Manual_controller_ch_active \t'
                            'Crank_angle_controller_ch_active \t'
                            'Thigh_angle_controller_ch_active \t'
                            'Knee_angle_controller_ch_active \t'
                            'BS_Gonio_controller_ch_active \t'
                            'Observer_controller_ch_active \t'
                            'Active_Controller \t'
                            
                            # Comment
                            'Comment '
                            '\n')


    # Starts the Thread who is writing Data from the Queue to the File
    def start(self,exit_event):

        self.Status = 0

        self.write_Thread = Thread(name='Datalogger_Writing_Thread', target=self.thread_WriteToFile, args=(exit_event,))
        self.write_Thread.daemon = False
        self.write_Thread.start()

    # Puts a new Data Object into the Queue to be processed
    def logData(self, data):
        log = self.data2log(data)

        self.dataQueue.put(log)

    # Returns an object containing the current IMUSEF_Data to log
    def data2log(self, data):
        dummy_value = 0.0



        # Timestap
        if(self.TimeStamp_start == None):
            self.TimeStamp_start = data.timestamp

        log = self.formatNum2String(data.timestamp-self.TimeStamp_start, decimals = 4) + '\t'

        # Inputs
        log += self.formatNum2String(data.CyclingComputer_DATA.CrankAngle) + '\t'

        log += self.formatNum2String(data.IMU_DATA_wireless.CrankAngle) + '\t'
        log += self.formatNum2String(data.IMU_DATA_wired.leftThighAngle) + '\t'
        log += self.formatNum2String(data.IMU_DATA_wired.rightThighAngle) + '\t'
        log += self.formatNum2String(data.IMU_DATA_wired.leftKneeAngle) + '\t'
        log += self.formatNum2String(data.IMU_DATA_wired.rightKneeAngle) + '\t'

        # Cycling Computer Data
        log += self.formatNum2String(data.CyclingComputer_DATA.Speed) + '\t'
        log += self.formatNum2String(data.CyclingComputer_DATA.Distance) + '\t'
        log += self.formatNum2String(data.CyclingComputer_DATA.Cadence) + '\t'

        # Powermeter Data
        log += self.formatNum2String(data.PowerMeter_DATA.Torque_left) + '\t'
        log += self.formatNum2String(data.PowerMeter_DATA.Torque_right) + '\t'
        log += self.formatNum2String(data.PowerMeter_DATA.Torque_total) + '\t'
        log += self.formatNum2String(data.PowerMeter_DATA.CrankAngle) + '\t'
        log += self.formatNum2String(data.PowerMeter_DATA.Cadence) + '\t'
        log += self.formatNum2String(data.PowerMeter_DATA.Power) + '\t'

        # Instrumented Hometrainer Data
        log += self.formatNum2String(data.Hometrainer_DATA.Speed) + '\t'
        log += self.formatNum2String(data.Hometrainer_DATA.Distance) + '\t'
        log += self.formatNum2String(data.Hometrainer_DATA.Torque) + '\t'
        log += self.formatNum2String(data.Hometrainer_DATA.Power) + '\t'
        log += self.formatNum2String(data.Hometrainer_DATA.Power_AVG) + '\t'

        # Physiological Data
        log += self.formatNum2String(data.HeartRate, decimals =1) + '\t'

        # Stimulation Data
        log += self.formatNum2String(data.StimIntensity, decimals =1) + '\t'

        # Buttons
        log += '%i' % data.Button_LEFT + '\t'
        log += '%i' % data.Button_RIGHT + '\t'
        log += '%i' % data.Button_BOOST + '\t'
        log += '%i' % data.EmergencyButton_Pressed + '\t'

        # Processed Angle Data
        log += self.formatNum2String(data.ThighAngle_Controller_DATA.NormalizedAngle_Left) + '\t'
        log += self.formatNum2String(data.ThighAngle_Controller_DATA.NormalizedAngle_Right) + '\t'
        log += self.formatNum2String(data.KneeAngle_Controller_DATA.NormalizedAngle_Left) + '\t'
        log += self.formatNum2String(data.KneeAngle_Controller_DATA.NormalizedAngle_Right) + '\t'
        log += self.formatNum2String(data.Observer_Controller_DATA.Phase) + '\t'

        # Controller Data
        log += self.getStringFromChannels(data.Remote_Controller_DATA.activeChannels) + '\t'
        log += self.getStringFromChannels(data.Manual_Controller_DATA.activeChannels) + '\t'
        log += self.getStringFromChannels(data.CrankAngle_Controller_DATA.activeChannels) + '\t'
        log += self.getStringFromChannels(data.ThighAngle_Controller_DATA.activeChannels) + '\t'
        log += self.getStringFromChannels(data.KneeAngle_Controller_DATA.activeChannels) + '\t'
        log += '00000000' + '\t'    # Benoits Gonio Algorithm
        log += self.getStringFromChannels(data.Observer_Controller_DATA.activeChannels) + '\t'
        log += data.activeController + '\t'


        # Comment
        log += re.sub('\s+', ' ', data.comment)

        # Finish log
        log += '\n'

        # Reset Comment field
        data.comment = "";

        return log

    # Get binary string from active channels of controllers
    def getStringFromChannels(self, activeChannels):
        result_string = ''
        for channel_bool in activeChannels:
            result_string = result_string + str(int(channel_bool))
        return result_string

    # Returns a formated string of a given number.
    # Allowed decimals: 1,3 or 4
    # in case the number is 0.00000... only '0' is returned to safe filespace
    # in case the number is -1.00000... only '-1' is returned to safe filespace
    def formatNum2String(self, num, decimals = 3):

        if num == 0.0:
            return '0'
        if num == -1.0:
            return '-1'


        if decimals == 1:
            return ('%.1f' % num)
        elif decimals == 4:
            return ('%.4f' % num)

        return ('%.3f' % num)


    # Removes Data first inserted
    def getDatatoWrite(self):
        return self.dataQueue.get(True, 0.5)

    # Writes Data to File
    def thread_WriteToFile(self, exit_event):

        self.Status = 1

        while not exit_event.isSet():
            try:
                # Get data
                row = self.getDatatoWrite()
                self.datafile.write(row)

            except Exception as e:
                #print(e)
                pass


        # Close up
        print('Log file successfully saved to: ' + self.file_path)
        self.datafile.close()

        self.Status = -1




if __name__ == '__main__':

    imusef_data1 = IMUSEF_Data()
    imusef_data2 = IMUSEF_Data()

    data1 = IMU_Data_wired()
    data1.leftKneeAngle = 1.0;

    data2 = IMU_Data_wired()
    data2.leftKneeAngle = 2.0;

    imusef_data1.IMU_DATA_wired = data1
    imusef_data1.IMU_DATA_wired = data1

    event = Event()

    myDatalogger = DataLogger()
    myDatalogger.start(event)

    i = 0
    try:
        while True:
            i+=1
            #print(str(i) + ") Working")

            imusef_data1.timestamp = time.time()
            myDatalogger.logData(imusef_data1)

            time.sleep(0.01)

            imusef_data2.timestamp = time.time()
            myDatalogger.logData(imusef_data2)

            time.sleep(0.01)

    except KeyboardInterrupt:
        event.set()





