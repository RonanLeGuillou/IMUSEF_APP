import sys
import glob
import serial
from opendaq import *
import time
import os


def serial_ports():
    ports = glob.glob('/dev/tty[A-Za-z]*')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def updatePosition(_pos):

    if(_pos<0):
        daq.init_pwm(0, 10000)
        daq.stop_pwm()
        return

    min = 500
    max = 2500
    periode = 10000

    PhW = min + (max-min) * (_pos/100.0)

    duty = (PhW/periode) *1023

    daq.init_pwm(round(duty), round(periode))
    print("Position: " + str(_pos))

#print (str(serial_ports()));








## Start of TestProgramm
daq = DAQ('/dev/OPENDAQ')
#daq.conf_adc(pinput=6, ninput=0, gain=Gains.S.x1, nsamples=1)
#daq.conf_adc(pinput=7, ninput=0, gain=Gains.S.x1, nsamples=1)
#daq.conf_adc(pinput=8, ninput=0, gain=Gains.S.x1, nsamples=1)

stream_exp = daq.create_stream(ExpMode.ANALOG_IN, 1, continuous=True)
stream_exp.analog_setup(pinput=8, ninput=0, gain=Gains.M.x1)



try:

    start = time.time()
    i = 0
    data = []
    daq.start()

    start = time.time()
    while (time.time() - start) <=3:
        time.sleep(0.01)

        for x in stream_exp.read():
            data.append(x)

    daq.stop()


    print("Samplerate: " + str(len(data)/3) + " Samples per second")

    daq.stop()

except KeyboardInterrupt:
    #daq.stop_pwm()
    daq.close()
    print ("Closed nicely");