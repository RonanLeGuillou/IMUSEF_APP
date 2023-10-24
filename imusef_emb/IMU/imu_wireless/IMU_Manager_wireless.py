# -*- coding: utf-8 -*-
"""
This class allows to run the data-aquisition of the wired IMU´s in an indepentend
Process. The processed data can be accessed by using the individual functions

@author: Martin Schmoll(CAMIN TEAM - INRIA)
"""
import numpy as np
from IMU_Data_wireless import *
from sensbiotk.transforms3d import quaternions as q
from sensbiotk.transforms3d import eulerangles as euler
import scripts.imu_dump_full_mod as imu_fox
import time
import threading
import sys

class IMU_Manager_wireless(object):

    # Constructor
    def __init__(self):

        # Data Container
        self.imu_data = IMU_Data_wireless()

        # Processing variables
        self.__quat_crank_offset = [0, 0, 0]
        self.__CrankAngle = 0.0


    # Starts a new Process for initialisation of the IMUs and data acquisition
    def start(self, exit_Event):

        self.exit_Event = exit_Event

        # Connect to IMU FOX device
        # TODO: Eventually put into different Process: -> involves changes in imu_dump_full_mod.py
        self.thread_imu_fox = threading.Thread(name="IMU_wireless_Thread", target=imu_fox.main, args=(self.exit_Event,))
        self.thread_imu_fox.daemon = True
        self.thread_imu_fox.start()

        time.sleep(0.1)


    # Stops the Process
    def stop(self):

        self.exit_Event.set()
        print("Wireless IMU stopped: Au revoir")

    # Initializes recalibration of the system
    def calibrate(self):
        self.__quat_crank_offset = [0, 0, 0]

    # Reads and processes the currenty available data
    def update(self):

        # Nothing to process because IMU_FOX is not ready
        if imu_fox.READY == False:
            self.__CrankAngle = 0
            return

        # Read and process new Values
        try:
            quat = euler.euler2quat(imu_fox.heading * np.pi / 180, imu_fox.attitude * np.pi / 180,
                                    imu_fox.bank * np.pi / 180)

            # Init
            if self.__quat_crank_offset == [0, 0, 0]:
                self.__quat_crank_offset = quat


            # Normal Operation
            else:
                quat = q.mult(q.conjugate(self.__quat_crank_offset), quat)


            # Update Values
            self.__CrankAngle = (euler.quat2euler2(quat)[0]) * 180 / np.pi


            # Necessary for artifacts
            while self.__CrankAngle < 0:
                self.__CrankAngle = 360 + self.__CrankAngle

                # Optional but here for the principle of it.
            while self.__CrankAngle > 360:
                self.__CrankAngle = self.__CrankAngle - 360



        except Exception as error:
            print(error)


    # Returns the current Crank Angle
    def getCrankAngle(self):
        self.update()
        return self.__CrankAngle



    # Returns all IMU_wireless_Data
    def getIMU_Data_wireless(self):
        self.imu_data.CrankAngle = self.getCrankAngle()
        return self.imu_data

    # Returns if the IMU Module is ready to use
    def getStatus(self):
        return imu_fox.READY


if __name__ == '__main__':

    e = threading.Event()

    myIMU_Manager = IMU_Manager_wireless()
    myIMU_Manager.start(e)

    i = 0
    try:
        while True:

            if(myIMU_Manager.getStatus()):

#                print(myIMU_Manager.getCrankAngle())
                sys.stdout.write('\r' + str(myIMU_Manager.getCrankAngle()) + ' ' * 10)
                sys.stdout.flush() # important

                time.sleep(0.05)
                i += 1
            else:
                print("IMUs not ready - please wait!")
                time.sleep(1)

            #if(i == 1000):
              #  print ("Stop IMUS")
               # myIMU_Manager.stop()
    except KeyboardInterrupt:
        print("\nExiting from KeyboardInterrupt")
        e.set()
        time.sleep(0.2)
        print('STOP')