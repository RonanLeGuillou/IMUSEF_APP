# Simple Adafruit BNO055 sensor reading example.  Will print the orientation
# and calibration data every second.
#
# Copyright (c) 2015 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import logging
import sys
import time
import numpy as np
import threading
import scipy.io as sio
import os

import sensbiotk.transforms3d.eulerangles as euler
from sensbiotk.transforms3d import quaternions as nq

try:
    from Adafruit_BNO055 import BNO055
    import multiplex

    BNO_READY = True
except ImportError:
    BNO_READY = False


def my_sleep(duration):
    time2sleep = time.time() + duration;
    while time.time() < time2sleep:
        time.sleep(0.0001)


# real_duration = time.time() - start
# return real_duration


class IMUS(object):

    def __init__(self):
        self.nb_imus = 4
        self.bno = {}
        self.sys = {1: 0, 2: 0, 3: 0, 4: 0}
        self.gyro = {1: 0, 2: 0, 3: 0, 4: 0}
        self.mag = {1: 0, 2: 0, 3: 0, 4: 0}
        self.accel = {1: 0, 2: 0, 3: 0, 4: 0}
        self.quat = {}
        self.yaw = {}
        self.pitch = {}
        self.roll = {}
        self.ax = {}
        self.ay = {}
        self.az = {}
        self.gx = {}
        self.gy = {}
        self.gz = {}
        ## Bus initialisation below moved to start of config
        self.bus = {}
        # self.bus = multiplex.init_i2c_bus()
        self.pi = np.pi
        self.r_k_angle = 0
        self.l_k_angle = 0
        self.BNO_READY = BNO_READY
        self.input_timestamp = 0
        # ~ print("\nInitialization of IMUS completed.\n")

    def config(self):
        if not BNO_READY:
            print("Cannot begin communication with the IMUs. Libraries unavailable")
            return False
        self.bus = multiplex.init_i2c_bus()

        # Create and configure the BNO sensor connection.
        for i in range(1, self.nb_imus + 1):
            multiplex.sw_channel(self.bus, channel=i)
            self.bno[i] = BNO055.BNO055()
            # Enable verbose debug logging if -v is passed as a parameter.
            if len(sys.argv) == 2 and sys.argv[1].lower() == '-v':
                logging.basicConfig(level=logging.DEBUG)
            # Initialize the BNO055 and stop if something went wrong.
            if not self.bno[i].begin():
                raise RuntimeError('Failed to initialize BNO055! Is the sensor ' + str(i) + ' connected?')

            # Print system status and self test result.
            status, self_test, error = self.bno[i].get_system_status()
            print('System status: {0}'.format(status))
            print('Self test result (0x0F is normal): 0x{0:02X}'.format(self_test))
            # Print out an error if system status is in error mode.
            if status == 0x01:
                print('System error: {0}'.format(error))
                print('See datasheet section 4.3.59 for the meaning.')

            # Print BNO055 software revision and other diagnostic data.
            sw, bl, accel, mag, gyro = self.bno[i].get_revision()
            print('Software version:   {0}'.format(sw))
            print('Bootloader version: {0}'.format(bl))
            print('Accelerometer ID:   0x{0:02X}'.format(accel))
            print('Magnetometer ID:    0x{0:02X}'.format(mag))
            print('Gyroscope ID:       0x{0:02X}\n'.format(gyro))

            print('Reading BNO055 number: ' + str(i) + ' data, press Ctrl-C to quit...')

    def calibration(self):
        calib_data = {}
        while not (self.sys[1] == 3 and self.sys[2] == 3 and self.sys[3] == 3 and self.sys[4] == 3):
            print('CALIB STATUS (SYS, GYRO, ACC, MAG), 3 = CALIBRATED')
            for i in range(1, self.nb_imus + 1):
                multiplex.sw_channel(self.bus, channel=i)
                # Read the calibration status, 0=uncalibrated and 3=fully calibrated.
                self.sys[i], self.gyro[i], self.accel[i], self.mag[i] = self.bno[i].get_calibration_status()
                # Print everything out.
            print('IMUs:' + str(1) + '\t' + str([self.sys[1], self.gyro[1], self.accel[1], self.mag[1]]) + '\n' + \
                  'IMUs:' + str(2) + '\t' + str([self.sys[2], self.gyro[2], self.accel[2], self.mag[2]]) + '\n' + \
                  'IMUs:' + str(3) + '\t' + str([self.sys[3], self.gyro[3], self.accel[3], self.mag[3]]) + '\n' + \
                  'IMUs:' + str(4) + '\t' + str([self.sys[4], self.gyro[1], self.accel[4], self.mag[4]]) + '\n')
            time.sleep(1)
        print('CALIBRATION SUCCESS')
        for i in range(1, self.nb_imus + 1):
            multiplex.sw_channel(self.bus, channel=i)
            calib_data[str(i)] = self.bno[i].get_calibration()
        dir = os.path.dirname(os.path.abspath(__file__))+"/"
        sio.savemat(dir+'calib_data.mat', calib_data)

    def load_calibration(self, data):
        for i in range(1, self.nb_imus + 1):
            multiplex.sw_channel(self.bus, channel=i)
            self.bno[i].set_calibration(data)
        print('CALIBRATION LOADED')

    def load_calibration_from_file(self, path='calib_data.mat'):
        dir = os.path.dirname(os.path.abspath(__file__))+"/"
        calib_data = sio.loadmat(dir+path)
        for i in range(1, self.nb_imus + 1):
            multiplex.sw_channel(self.bus, channel=i)
            self.bno[i].set_calibration(list(calib_data[str(i)][0]))
        print('CALIBRATION LOADED')

    def thread_knee_angles(self, e):
        while not e.isSet():
            self.read_knee_angles()
            # ~ time.sleep(0.001)
            my_sleep(0.001)

    def thread_knee_angles_and_gyr(self, e):
        while not e.isSet():
            self.read_knee_angles_and_gyr()
            # ~ time.sleep(0.001)
            my_sleep(0.001)

    def thread_knee_angles_acc_gyr_euler(self, e):
        while not e.isSet():
            self.read_knee_angles_acc_gyr_euler()
            # ~ time.sleep(0.001)
            my_sleep(0.001)

    def read_euler_from_id_imu(self, id_imu):
        multiplex.sw_channel(self.bus, channel=id_imu)
        return self.bno[id_imu].read_euler()

    def read_knee_angles(self):
        for i in range(1, self.nb_imus + 1):
            multiplex.sw_channel(self.bus, channel=i)
            # Read the calibration status, 0=uncalibrated and 3=fully calibrated.
            #        sys[i], gyro[i], accel[i], mag[i] = bno[i].get_calibration_status()
            # Orientation as a quaternion:
            q = self.bno[i].read_quaternion()
            # Change of frame for standard 3D representations
            #                    quat[i] = [q[0], -q[2], q[1], -q[3]] DEPRECATED
            self.quat[i] = [q[0], q[1], q[2], q[3]]
            # Quat between IMUs 1 and 2
        q1_to_2 = nq.mult(nq.conjugate(self.quat[1]), self.quat[2])
        # Conversion to Euler Angles
        [z_angle_1_to_2, _, _] = euler.quat2euler4(q1_to_2)
        self.r_k_angle = z_angle_1_to_2 * 180 / self.pi
        # Quat between IMUs 3 and 4
        q3_to_4 = nq.mult(nq.conjugate(self.quat[3]), self.quat[4])
        # Conversion to Euler Angles
        [z_angle_3_to_4, _, _] = euler.quat2euler4(q3_to_4)
        self.l_k_angle = z_angle_3_to_4 * 180 / self.pi

    def read_knee_angles_and_gyr(self):
        for i in range(1, self.nb_imus + 1):
            multiplex.sw_channel(self.bus, channel=i)
            # Orientation as a quaternion:
            q = self.bno[i].read_quaternion()
            # Change of frame for standard 3D representations
            #                    quat[i] = [q[0], -q[2], q[1], -q[3]] DEPRECATED
            self.quat[i] = [q[0], q[1], q[2], q[3]]
            # Read the gyrometer values
            [self.gx[i], self.gy[i], self.gz[i]] = self.bno[i].read_gyroscope()
        # Quat between IMUs 1 and 2
        q1_to_2 = nq.mult(nq.conjugate(self.quat[1]), self.quat[2])
        # Conversion to Euler Angles
        [z_angle_1_to_2, _, _] = euler.quat2euler4(q1_to_2)
        self.r_k_angle = z_angle_1_to_2 * 180 / self.pi
        # Quat between IMUs 3 and 4
        q3_to_4 = nq.mult(nq.conjugate(self.quat[3]), self.quat[4])
        # Conversion to Euler Angles
        [z_angle_3_to_4, _, _] = euler.quat2euler4(q3_to_4)
        self.l_k_angle = z_angle_3_to_4 * 180 / self.pi

    def read_knee_angles_acc_gyr_euler(self):
        for i in range(1, self.nb_imus + 1):
            multiplex.sw_channel(self.bus, channel=i)
            # Orientation as a quaternion:
            q = self.bno[i].read_quaternion()
            # Change of frame for standard 3D representations
            #                    quat[i] = [q[0], -q[2], q[1], -q[3]] DEPRECATED
            self.quat[i] = [q[0], q[1], q[2], q[3]]
            # Read the gyrometer values
            [self.gx[i], self.gy[i], self.gz[i]] = self.bno[i].read_gyroscope()
            # Read the AHRS angles
            [self.yaw[i], self.roll[i], self.pitch[i]] = self.bno[i].read_euler()
            # Read the accelerometer values
            [self.ax[i], self.ay[i], self.az[i]] = self.bno[i].read_accelerometer()

        # Quat between IMUs 1 and 2
        q1_to_2 = nq.mult(nq.conjugate(self.quat[1]), self.quat[2])
        # Conversion to Euler Angles
        [z_angle_1_to_2, _, _] = euler.quat2euler4(q1_to_2)
        self.r_k_angle = z_angle_1_to_2 * 180 / self.pi
        # Quat between IMUs 3 and 4
        q3_to_4 = nq.mult(nq.conjugate(self.quat[3]), self.quat[4])
        # Conversion to Euler Angles
        [z_angle_3_to_4, _, _] = euler.quat2euler4(q3_to_4)
        self.l_k_angle = z_angle_3_to_4 * 180 / self.pi
        if not self.input_timestamp:
            self.input_timestamp = time.time()

    def thread_file_input_emulation(self, e, input_file_name, start_event, period_in_sec=0):
        self.pedal_angle = 0
        self.data_line_timestamp = 0

        with open(input_file_name, "r+") as input_file:
            ## Reading header
            header_line = input_file.readline()
            if header_line == '':
                print ("\nEmpty Input File : %s\n", input_file_name)

            else:  ## Then start reading the data
                ## First, read the first line and still make sure its not the only one
                data_line = input_file.readline()
                if data_line == '':
                    print ("\nEmpty Input File after first data_line: %s\n", input_file_name)
                    e.set()

                ##Pre split the first line
                data_line_splited = data_line.split()

                time_offset = 0

                while not e.isSet():

                    ## Call the line process fonction
                    self.read_line_of_input_file(data_line_splited)
                    if not start_event.isSet():
                        print('waiting for start event')
                        start_event.wait(10)
                        print('start event set, reading the file')
                        ## Create an offset to correspond to the input timestamps
                        # ~ my_sleep(0.01)
                        time_offset = time.time() - float(
                            data_line_splited[0]) - 0.0125  # Offset to synchronize the data
                        self.data_line_timestamp = float(data_line_splited[0])

                    ## Get the next line and compute with the previous line the time to sleep between the two
                    next_data_line = input_file.readline()
                    # ~ print(data_line)
                    if next_data_line == '':
                        print ("\nEnd Of File : %s\n", input_file_name)
                        break
                    ## Pre split next line and use the timestamp
                    next_line_splited = next_data_line.split()

                    ## Get the next timestamp
                    # ~ last_timestamp = next_timestamp
                    next_timestamp = float(next_line_splited[0])

                    ## Get the difference between the next one and the current one
                    # ~ auto_period_to_sleep = next_timestamp - self.data_line_timestamp
                    ## Getting the elapsed_time since the start of the reading
                    elapsed_time = time.time() - time_offset
                    # ~ print("diff time : ", elapsed_time-self.data_line_timestamp,"diff time nextTS: ",next_timestamp - elapsed_time)
                    ## Concluding the time left until the new line of data is supposed to arrive
                    auto_period_to_sleep = next_timestamp - elapsed_time
                    # ~ auto_period_to_sleep = next_timestamp - last_timestamp

                    data_line_splited = next_line_splited
                    # ~ print(self.roll[3])
                    if auto_period_to_sleep > 0:
                        if period_in_sec:  # Use given period
                            # ~ time.sleep(period_in_sec)
                            my_sleep(period_in_sec)
                        else:  # Use Autoperiod
                            # ~ print("auto_period_to_sleep : ",auto_period_to_sleep)
                            # ~ time.sleep(auto_period_to_sleep)
                            my_sleep(auto_period_to_sleep)
                    else:
                        print("Did not sleep on imu emulator. already late. Trying to get back to it")

        ## If the end was no provoked by the end event, it was provoked by the input file
        ## So raise interrupt so the program ends. The file will be closed by the "with open"
        ## Otherwise do nothing and leave
        if not e.isSet():
            print ("\nSetting end Event from LibIMU to stop the program\n")
            e.set()
            # ~ print ("\nRaising KeyboardInterrupt from LibIMU to stop the program\n")
            # ~ raise KeyboardInterrupt

    def get_pedal_angle(self):
        return self.pedal_angle

    def get_input_timestamp(self):
        return self.input_timestamp

    def set_input_timestamp(self, value):
        self.input_timestamp = value

    def get_data_line_timestamp(self):
        return self.data_line_timestamp

    # ~ def read_line_of_input_file(self, data_line):
    def read_line_of_input_file(self, splited_line):
        # ~ splited_line = data_line.split()

        ## Shared timer for external cascade timing
        if not self.input_timestamp:
            self.input_timestamp = time.time()

        self.data_line_timestamp = float(splited_line[0])
        self.l_k_angle = float(splited_line[1])
        self.r_k_angle = float(splited_line[2])
        self.roll[3] = float(splited_line[3])  ## Left thigh angle
        self.roll[1] = float(splited_line[4])  ## Right thigh angle

        self.pedal_angle = float(splited_line[5])

        self.gy[3] = float(splited_line[6])  ## Left Gyr
        self.gy[1] = float(splited_line[7])  ## Right Gyr

        start = 8
        for i in range(1, self.nb_imus + 1):
            self.ax[i] = float(splited_line[start + (i - 1) * 3])
            self.ay[i] = float(splited_line[start + 1 + (i - 1) * 3])
            self.az[i] = float(splited_line[start + 2 + (i - 1) * 3])

        # self.ax[1] = float(splited_line[8])
        # self.ay[1] = float(splited_line[9])
        # self.az[1] = float(splited_line[10])

        # self.ax[2] = float(splited_line[11])
        # self.ay[2] = float(splited_line[12])
        # self.az[2] = float(splited_line[13])

        # self.ax[3] = float(splited_line[14])
        # self.ay[3] = float(splited_line[15])
        # self.az[3] = float(splited_line[16])

        # self.ax[4] = float(splited_line[17])
        # self.ay[4] = float(splited_line[18])
        # self.az[4] = float(splited_line[19])


if __name__ == '__main__':
    imus = IMUS()
    imus.config()
    e = threading.Event()
    thread_angles = threading.Thread(target=imus.thread_knee_angles, args=(e,))

    try:
        thread_angles.start()
        while True:
            print("r_k_angle: " + str(imus.r_k_angle) + "\t l_k_angle: " + str(imus.l_k_angle))
            time.sleep(0.010)
    except KeyboardInterrupt:
        print('STOP')
        e.set()
