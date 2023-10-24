# -*- coding: utf-8 -*-
"""
This class allows to run the data-aquisition of the wired IMU´s in an indepentend
Process. The processed data can be accessed by using the individual functions

@author: Martin Schmoll(CAMIN TEAM - INRIA)
"""

from LibIMU import *
from IMU_Data_wired import *
from multiprocessing import Process, Value, Array


class IMU_Manager(object):

    # Constructor
    def __init__(self):

        # Status flags
        self.IMUs_READY = Value('i', 0)
        self.killProcess = Value('i', 0)

        # Data to read via the specific functions
        self.leftKneeAngle = Value('d', 0.0)
        self.rightKneeAngle = Value('d', 0.0)

        self.leftThighAngle = Value('d', 0.0)
        self.rightThighAngle = Value('d', 0.0)

        self.IMU_timestamp = Value('d', 0.0)

        # RAW-Data
        self.gx = Array('d', 4)
        self.gy = Array('d', 4)
        self.gz = Array('d', 4)
        self.ax = Array('d', 4)
        self.ay = Array('d', 4)
        self.az = Array('d', 4)

        # Data Container
        self.imu_data = IMU_Data_wired()


    # Starts a new Process for initialisation of the IMUs and data acquisition
    def start(self):
        self.read_Process = Process(target=self.process_run, args=())
        self.read_Process.daemon = True
        self.read_Process.start()


    # Stops the Process
    def stop(self):
        self.killProcess.value = 1
        self.read_Process.terminate()


    # Function to run the process
    def process_run(self):

        # Create new IMU object
        imus = IMUS()
        imus.config()
        imus.load_calibration_from_file()

        # After successful configuration set Flag to True
        if(imus.BNO_READY):
            self.IMUs_READY.value = 1

        # Main-Loop
        try:
            while not self.killProcess.value == 1:
                # Read new Values
                imus.read_knee_angles_acc_gyr_euler()

                # Transfer values to IMU-Manager Class
                self.leftKneeAngle.value = imus.l_k_angle
                self.rightKneeAngle.value = imus.r_k_angle

                self.leftThighAngle.value = imus.roll[3]
                self.rightThighAngle.value = imus.roll[1]

                self.IMU_timestamp.value = imus.get_input_timestamp()

                self.gx[0] = imus.gx[1]
                self.gx[1] = imus.gx[2]
                self.gx[2] = imus.gx[3]
                self.gx[3] = imus.gx[4]

                self.gy[0] = imus.gy[1]
                self.gy[1] = imus.gy[2]
                self.gy[2] = imus.gy[3]
                self.gy[3] = imus.gy[4]

                self.gz[0] = imus.gz[1]
                self.gz[1] = imus.gz[2]
                self.gz[2] = imus.gz[3]
                self.gz[3] = imus.gz[4]

                self.ax[0] = imus.ax[1]
                self.ax[1] = imus.ax[2]
                self.ax[2] = imus.ax[3]
                self.ax[3] = imus.ax[4]

                self.ay[0] = imus.ax[1]
                self.ay[1] = imus.ax[2]
                self.ay[2] = imus.ax[3]
                self.ay[3] = imus.ax[4]

                self.az[0] = imus.az[1]
                self.az[1] = imus.az[2]
                self.az[2] = imus.az[3]
                self.az[3] = imus.az[4]

                time.sleep(0.001)
                #my_sleep(0.001)
        except KeyboardInterrupt:
            #print("Keyboard Interrupt...:")
            pass

        print("IMUs stopped: Au revoir")
        self.IMUs_READY.value = 0

    # Returns the left Knee Angle
    def getLeftKneeAngle(self):
        return self.leftKneeAngle.value


    # Returns the right Knee Angle
    def getRightKneeAngle(self):
        return self.rightKneeAngle.value

    # Returns the left Thigh Angle
    def getLeftThighAngle(self):
        return self.leftThighAngle.value


    # Returns the right Thigh Angle
    def getRightThighAngle(self):
        return self.rightThighAngle.value


    # Returns the RAW-data of the Accelerometers in X-direction
    def getAx(self):
        return {1:self.ax[0], 2:self.ax[1], 3:self.ax[2], 4:self.ax[3]}


    # Returns the RAW-data of the Accelerometers in Y-direction
    def getAy(self):
        return {1:self.ay[0], 2:self.ay[1], 3:self.ay[2], 4:self.ay[3]}


    # Returns the RAW-data of the Accelerometers in Z-direction
    def getAz(self):
        return {1:self.az[0], 2:self.az[1], 3:self.az[2], 4:self.az[3]}

    # Returns the RAW-data of the Gyroscopes in X-direction
    def getGx(self):
        return {1: self.gx[0], 2: self.gx[1], 3: self.gx[2], 4: self.gx[3]}

    # Returns the RAW-data of the Gyroscopes in Y-direction
    def getGy(self):
        return {1: self.gy[0], 2: self.gy[1], 3: self.gy[2], 4: self.gy[3]}

    # Returns the RAW-data of the Gyroscopes in Z-direction
    def getGz(self):
        return {1: self.gz[0], 2: self.gz[1], 3: self.gz[2], 4: self.gz[3]}


    # Returns all IMU_Data
    def getIMU_Data_wired(self):

        self.imu_data.IMU_timestamp = self.IMU_timestamp.value

        self.imu_data.leftKneeAngle = self.getLeftKneeAngle()
        self.imu_data.rightKneeAngle = self.getRightKneeAngle()

        self.imu_data.leftThighAngle = self.getLeftThighAngle()
        self.imu_data.rightThighAngle = self.getRightThighAngle()

        self.imu_data.ax = self.getAx()
        self.imu_data.ay = self.getAy()
        self.imu_data.az = self.getAz()

        self.imu_data.gx = self.getGx()
        self.imu_data.gy = self.getGy()
        self.imu_data.gz = self.getGz()

        return self.imu_data

    # Returns if the IMU Modules are ready to use
    def getIMUsReady(self):
        return (self.IMUs_READY.value == 1)


if __name__ == '__main__':

    myIMU_Manager = IMU_Manager()
    myIMU_Manager.start()

    i = 0
    try:
        while True:
            #print("Left: "+str(IMU_Manager.getLeftKneeAngle()) + "\t Right: "+str(IMU_Manager.getRightKneeAngle()))
            #print("Right Thigh Angle" + imus.getRightThighAngle())
            if(myIMU_Manager.getIMUsReady()):
                #print( str(i) +") Left Thigh: " + str(myIMU_Manager.getLeftThighAngle())+ " Right Thigh: ") +str(myIMU_Manager.getRightThighAngle())
                data = myIMU_Manager.getIMU_Data_wired()
                print(data.leftKneeAngle)

                time.sleep(0.1)
                i += 1
            else:
                print("IMUs not ready - please wait!")
                time.sleep(1)

            if(i == 1000):
                print ("Stop IMUS")
                myIMU_Manager.stop()
    except KeyboardInterrupt:
        print('STOP')


