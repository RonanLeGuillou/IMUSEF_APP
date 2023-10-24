#~ data_analyser.py
import csv
import matplotlib.pyplot as plt
import numpy as np
import os, sys
#~ from scipy.fftpack import fft, fftfreq
#~ import scipy.signal
#~ import pyqtgraph as pg


def analyse_courbes():

    ## If version is python3 replace raw_input by input
    #if sys.version_info[0] == 3:
        #raw_input = input
    try :
        number = input("Enter file number \n")
    except :
        number = raw_input("Enter file number \n")
    
    hometrainer_file = 'hometrainer_data'+str(number)+'.txt'

    donnees_HT = open(hometrainer_file,"r+") 
    header_line = donnees_HT.readline()
    first_line = donnees_HT.readline()

    

    time_power=[]
    power=[]
    HT_RPM=[]
    BikeKmh=[]
    counter = []
    encoder=[]
# self.log_file.write('Time Counter Encoder AnalogTorque Torque HT_Rpm RW_Rpm Power BikeKm/h\n')

    while True :
        line_HT = donnees_HT.readline()
        #~ line.replace(',','.')
        if line_HT == '':
            print ("\nEnd Of HomeTrainer File\n")
            break

        splited_line = line_HT.split()

        time_power.append(float(splited_line[0]))
        power.append(float(splited_line[7]))
        HT_RPM.append(float(splited_line[5]))
        BikeKmh.append(float(splited_line[8]))
        encoder.append(float(splited_line[2]))
        counter.append(float(splited_line[1]))
        
            
    donnees_HT.close()

    plt.figure()
    plt.grid()
    plt.title('Power')
    plt.plot(time_power, power)
    plt.xlabel('Temps (s)'); plt.ylabel('Power W')
    
    plt.figure()
    plt.grid()
    plt.title('counter')
    plt.plot(time_power, counter)
    plt.xlabel('Temps (s)'); plt.ylabel('counter')

    plt.figure()
    plt.grid()
    plt.title('encoder')
    plt.plot(time_power, encoder)
    plt.xlabel('Temps (s)'); plt.ylabel('encoder')

    plt.figure()
    plt.grid()
    plt.title('HT_RPM')
    plt.plot(time_power, HT_RPM)
    plt.xlabel('Temps (s)'); plt.ylabel('HT_RPM ')


    plt.figure()
    plt.grid()
    plt.title('BikeKmh')
    plt.plot(time_power, BikeKmh)
    plt.xlabel('Temps (s)'); plt.ylabel('BikeKmh ')
    # plt.figure()
    # plt.grid()
    # plt.title('Phase brute')
    # for i in range (1,len(power_segmented)-1) :
    #     plt.plot(power_segmented_x[i],power_segmented[i], color=(0.8-i/1800, 0.2, 0.1))
    # plt.xlabel('Samples of segmented power by turn'); plt.ylabel('Power W')


    # plt.figure()
    # plt.grid()
    # plt.title('Phase brute')
    # plt.plot(time_angle, phase)
    # plt.xlabel('Temps (s)'); plt.ylabel('Phase (Percent)')

    plt.show()



if __name__ == '__main__':

    analyse_courbes()
