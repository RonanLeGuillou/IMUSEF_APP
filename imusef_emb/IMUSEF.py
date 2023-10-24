# -*- coding: utf-8 -*-
"""
IMUSEF - 4 wired IMUs and a BerkelBike Stimulator

@author: Benoît SIJOBERT &RLG &Morten (CAMIN TEAM - INRIA)

"""
from openANT.myOpenANT_Manager import myOpenAnt_Manager
from openDAQ.myDAQManager import myDAQManager
from Stimulators.FESBox_Manager import FESBox_Manager
from HomeTrainer.Hometrainer import *
from openDAQ.myCrankAngleEncoder import myCrankAngleEncoder
from myGPIO.GPIO_Manager import GPIO_Manager
from UDP.UDP_Server import UDP_Server
from TCP.TCP_Server import TCP_Server
from TCP.TCP_Message import TCP_Message
from Controllers.Manual_Controller import Manual_Controller
from Controllers.Gonio_ThighAngle_Controller import Gonio_ThighAngle_Controller
from Controllers.Gonio_KneeAngle_Controller import Gonio_KneeAngle_Controller
from Controllers.CrankAngle_Controller import CrankAngle_Controller
from Controllers.Observer_Controller import Observer_Controller
from Controllers.TCP_Controller import TCP_Controller
from Controllers.Biodex_Controller import Biodex_Controller
from IMU.imu_wired.LibIMU import *
from IMU.imu_wired.IMU_Manager import IMU_Manager
from IMU.imu_wireless.IMU_Manager_wireless import IMU_Manager_wireless
from DataLogger.DataLogger import DataLogger
from IMUSEF_Data import IMUSEF_Data


import json
import numpy as np
from CyclingComputer.CyclingComputer import CyclingComputer
import traceback
import sys

# Constants
CONTROLLER_NONE = "CONTROLLER_NONE"                 # No Controller is selected to controll the stimulator
CONTROLLER_TCP = "CONTROLLER_TCP"                   # Stimulator is controlled by the TCP-Client (testing and configuration)
CONTROLLER_CRANKANGLE = "CONTROLLER_CRANKANGLE"     # Stimulator is controlled my the CrankAngle Controller
CONTROLLER_THIGHANGLE = "CONTROLLER_THIGHANGLE"     # Stimulator is controlled my the ThighAngle Controller
CONTROLLER_KNEEANGLE = "CONTROLLER_KNEEANGLE"       # Stimulator is controlled my the KneeAngle Controller
CONTROLLER_OBSERVER = "CONTROLLER_OBSERVER"         # Stimulator is controlled my the Observer Controller
CONTROLLER_BIODEX = "CONTROLLER_BIODEX"             # Stimulator is controlled my the Biodex Controller


class IMUSEF(object):

    # Initialisation
    def __init__(self, Watchdog_Monitoring = False):

        ## Settings

        # Activity flags - Basic Modules
        self.FLAG_LOG_DATA = False
        self.FLAG_UDP_SERVER = True
        self.FLAG_TCP_SERVER = True

        # Activity flags - Other Modules
        self.FLAG_RELAYBOX = False                     # If 'False' the channels will be switched via Bluetooth directly on the Berkelbike Stimulator
        self.FLAG_STIMULATOR = False
        self.FLAG_CRANKANGLE_SENSOR_OPENDAQ = False
        self.FLAG_CRANKANGLE_SENSOR_IMU_FOX = False
        self.FLAG_IMUs = True
        self.FLAG_HEARTRATE_MONITOR = False
        self.FLAG_POWERMETER_ROTOR = False
        self.FLAG_HOMETRAINER = False
        self.FLAG_BIODEX = False

        # Activate Controls
        self.FLAG_Emergency_Button = False
        self.FLAG_Left_Button = False
        self.FLAG_Right_Button = False
        self.FLAG_Boost_Button = False
        self.FLAG_Man_Auto_Switch = False

        # Watchdog
        self.Watchdog_Monitoring = Watchdog_Monitoring
        self.Keepalive_timer = time.time()
        self.Keepalive_delay = 0.25

        if(self.FLAG_BIODEX):
            self.FLAG_HOMETRAINER = False

        # Channels activated turing stimulation
        self.__UsedChannels = [True, True, True, True, True, True, True, True]


        # Define Simulation
        self.FLAG_SIMULATE_CRANKANGLE = False
        self.FLAG_SIMULATE_KNEEANGLES = False
        self.FLAG_SIMULATE_THIGHANGLES = False
        self.FLAG_SIMULATE_FROM_FILE = False

        # Define File Replay Simulation settings
        self.FLAG_SIMULATE_FROM_FILE_READY = False
        self.FLAG_DOUBLE_FILE_FREQUENCY = True
        self.input_sim_folder_name = "Controllers/cpg_working_ref/data/input/"
        self.input_sim_file_name = "JP_18_01_2019/datafile_13.txt"
        self.double_frequency_trick = False
        self.next_data_line_sim = ''
        self.previous_data_line_sim = ''

        # Simulation Settings
        self.__simulatedCadence = 50.0
        self.__sim_CrankAngleSpeed = (self.__simulatedCadence / 60.0) * 360.0  # Simulated CrankAngle Speed
        self.__sim_w = 2 * np.pi * (self.__simulatedCadence / 60.0)         # Simulated angular Velocity w
        self.__Min_Sim_KneeAngle = -120.0
        self.__Max_Sim_KneeAngle = -10.0
        self.__Min_Sim_ThighAngle = -60.0
        self.__Max_Sim_ThighAngle = -10.0

        # Define Port Numbers
        self.__UDP_PortNumber = 12345
        self.__UDP_Counter = 0
        self.__UDP_Divider = 1              # Put 0 to send all data
        self.__TCP_PortNumber = 12346


        # Event to exit the IMUSEF
        self.exit = threading.Event()
        self.stop_Datalogging = threading.Event()

        # Data Container
        self.data = IMUSEF_Data()

        # Define Modules
        self.myDataLogger = None
        self.myGPIO_Manager = GPIO_Manager(self.exit, RelayBox_active = self.FLAG_RELAYBOX)
        self.myUDP_Server = UDP_Server(self.__UDP_PortNumber)
        self.myTCP_Server = TCP_Server(self.__TCP_PortNumber)
        self.myFESBox_Manager = FESBox_Manager()
        self.myIMU_Manager_wireless = IMU_Manager_wireless()
        self.myIMU_Manager = IMU_Manager()
        self.myHometrainer = HOMETRAINER()
        self.myCrankAngleSensor = myCrankAngleEncoder()
        self.myCyclingComputer = CyclingComputer()
        self.myDAQManager = myDAQManager()
        self.myANT_Manager = myOpenAnt_Manager()

        # Device Addresses
        self.__MAC_Stimulator = ""
        self.__ID_Rotor_Powermeter = 0
        self.__ID_HeartRateMonitor = 0

        # Stimulator Variables
        self.Stimulator_TimeStamp_LastStatusRequest = 0.0   # TimeStamp of last Status Request
        self.Stimulator_StatusRequestInterval = 1.0         #[s] Seconds between Status requests

        # Define Control-Mode
        self.CONTROL_MODE = CONTROLLER_CRANKANGLE

        # Generate Controllers
        self.myManualController = Manual_Controller()
        self.__Max_Cadence_Manual_Control = 20  # RPM -> Maximal Cadence for manual Control

        self.myBiodexController = Biodex_Controller()
        self.myRemoteController = TCP_Controller()
        self.myCrankAngleController = CrankAngle_Controller()
        self.myThighAngleController = Gonio_ThighAngle_Controller()
        self.myKneeAngleController = Gonio_KneeAngle_Controller()
        self.myObserverController = Observer_Controller()

        # Define Config-File
        self.__ConfigFile = "Settings/ConfigFile.imusef"

        # Load Configuration from File
        self.__loadConfig()


        ## Activate Modules
        # Activate UDP-Server
        if self.FLAG_UDP_SERVER:
            self.myUDP_Server.start(self.exit)

        # Activate TCP-Server
        if self.FLAG_TCP_SERVER:
            self.myTCP_Server.start(self.exit)

        if self.FLAG_CRANKANGLE_SENSOR_IMU_FOX:
            self.myIMU_Manager_wireless.start(self.exit)

        # Start IMU_Manager
        if self.FLAG_IMUs:
            self.myIMU_Manager.start()

        # Start stimulator
        if self.FLAG_STIMULATOR:
            self.myFESBox_Manager.start(self.exit, self.__MAC_Stimulator)

        if self.FLAG_HOMETRAINER:
            self.myHometrainer.start()

        if self.FLAG_CRANKANGLE_SENSOR_OPENDAQ:
            self.myCrankAngleSensor.start()

        if self.FLAG_BIODEX:
            self.myDAQManager.start()

        if self.FLAG_POWERMETER_ROTOR:
            self.myANT_Manager.start(self.exit, self.__ID_Rotor_Powermeter, self.__ID_HeartRateMonitor)

        ## Init complete
        print("IMUSEF: Initialization Completed!")
        self.myGPIO_Manager.DoubleBeep()
        self.myGPIO_Manager.setSystemLED(True)

    # Main part of the program - Blocking!
    def run(self):

        # TODO: Remove general try-catch, be more specific and define clear shut-down criteria
        # TODO: This loop should run the entire time and even be restarted in case of error
        try:


            #################
            # - Main Loop - #
            #################

            while True:

                # New Cycle
                now = time.time()
                self.data.LoopTime = now - self.data.timestamp
                self.data.timestamp = now

                ## Anything new from the TCP_Client?
                if self.myTCP_Server.hasData():
                    msg = TCP_Message()
                    msg.parseFromString(self.myTCP_Server.getMessage())
                    self.__handleMessage(msg)


                ## Make a sound when the stimulator was reconfigured
                if self.myFESBox_Manager.BEEP_OK:
                    self.myGPIO_Manager.DoubleBeep()
                    self.myFESBox_Manager.BEEP_OK = False

                ## Notify Client if update of stimulation parameters was successfull or not
                if self.myFESBox_Manager.notify_Parameter_update:

                    # Update OK
                    if self.myFESBox_Manager.READY:
                        self.myGPIO_Manager.DoubleBeep()

                    # Update Failed
                    else:
                        self.myGPIO_Manager.Beep(0.5)

                    # Inform the TCP-Client
                    msg.buildMessage(TCP_Message.CMD_RE_SET_STIM_PARAMS, str(self.myFESBox_Manager.READY))
                    self.myTCP_Server.sendData(msg.toString())

                    # Reset notification
                    self.myFESBox_Manager.notify_Parameter_update = False

                ## Initialize Encoder - triggered by Z-Channel of Sensor
                if (self.myGPIO_Manager.ResetCrankAngle() and self.FLAG_CRANKANGLE_SENSOR_OPENDAQ):
                    self.myCrankAngleSensor.initEncoder()


                ## Read Buttons
                if self.FLAG_Left_Button:
                    self.data.Button_LEFT = self.myGPIO_Manager.getButton_LEFT()
                else:
                    self.data.Button_LEFT = -1

                if self.FLAG_Right_Button:
                    self.data.Button_RIGHT = self.myGPIO_Manager.getButton_RIGHT()
                else:
                    self.data.Button_RIGHT = -1

                if self.FLAG_Boost_Button:
                    self.data.Button_BOOST = self.myGPIO_Manager.getButton_BOOST()
                else:
                    self.data.Button_BOOST = -1

                if self.FLAG_Man_Auto_Switch:
                    self.data.Switch_MAN_AUTO = self.myGPIO_Manager.getSwitch_MAN_AUTO()
                else:
                    self.data.Switch_MAN_AUTO = -1

                if self.FLAG_Emergency_Button:
                    self.data.Button_Emergency = self.myGPIO_Manager.getButton_Emergency()
                else:
                    self.data.Button_Emergency = -1


                ## Read Data from Modules
                if self.FLAG_STIMULATOR and \
                  (self.Stimulator_TimeStamp_LastStatusRequest + self.Stimulator_StatusRequestInterval) < self.data.timestamp:
                    request_OK = self.myFESBox_Manager.requestAmplitude()

                    if request_OK:
                        self.Stimulator_TimeStamp_LastStatusRequest = self.data.timestamp

                self.data.StimIntensity = self.myFESBox_Manager.getStimulationIntensity()

                self.data.IMU_DATA_wired = self.myIMU_Manager.getIMU_Data_wired()
                self.data.IMU_DATA_wireless = self.myIMU_Manager_wireless.getIMU_Data_wireless()

                self.data.Hometrainer_DATA = self.myHometrainer.getData()

                self.data.HeartRate = self.myANT_Manager.getHeartRate()

                self.data.PowerMeter_DATA = self.myANT_Manager.getData()

                self.data.CyclingComputer_DATA.CrankAngle = self.myCrankAngleSensor.getEncoderValue()


                ## Simulate desired values
                if self.FLAG_SIMULATE_CRANKANGLE:
                    self.data.CyclingComputer_DATA.CrankAngle = (self.data.timestamp * self.__sim_CrankAngleSpeed) % 360;

                if self.FLAG_SIMULATE_KNEEANGLES:
                    A = (self.__Max_Sim_KneeAngle - self.__Min_Sim_KneeAngle) / 2
                    Base = self.__Min_Sim_KneeAngle + A
                    self.data.IMU_DATA_wired.leftKneeAngle = Base + A * np.sin(self.__sim_w * self.data.timestamp)
                    self.data.IMU_DATA_wired.rightKneeAngle = Base + A * np.sin(self.__sim_w * self.data.timestamp + np.pi)

                if self.FLAG_SIMULATE_THIGHANGLES:
                    A = (self.__Max_Sim_ThighAngle - self.__Min_Sim_ThighAngle) /2
                    Base = self.__Min_Sim_ThighAngle + A
                    self.data.IMU_DATA_wired.leftThighAngle = Base + A * np.sin(self.__sim_w * self.data.timestamp)
                    self.data.IMU_DATA_wired.rightThighAngle = Base + A * np.sin(self.__sim_w * self.data.timestamp + np.pi)

                ## OPTIONAL LINE TO TRIGGER REPLAY SIMULATION FROM THE INTERFACE
                # self.FLAG_SIMULATE_FROM_FILE = self.FLAG_SIMULATE_THIGHANGLES

                if self.FLAG_SIMULATE_FROM_FILE:
                    if not self.FLAG_SIMULATE_FROM_FILE_READY:
                        self.__setup_simulate_from_file()
                    self.__update_simulate_from_file()


                ## Update CyclingComputer
                self.myCyclingComputer.update( self.data.timestamp,
                                               self.data.CyclingComputer_DATA.CrankAngle,
                                               self.data.Hometrainer_DATA.Power,
                                               self.myGPIO_Manager.getSpeedTimeStamp())

                self.data.CyclingComputer_DATA = self.myCyclingComputer.getData()

                ## Update Controllers
                self.myRemoteController.update()

                # TODO: Activate if used: Deactivated 17.03.2020 - Morten
                # self.myBiodexController.update(self.myDAQManager.getPosition(), self.myDAQManager.getSpeed())

                self.myManualController.update(self.data.Button_LEFT, self.data.Button_RIGHT)

                self.myThighAngleController.update(self.data.timestamp, \
                                                   self.data.IMU_DATA_wired.leftThighAngle, \
                                                   self.data.IMU_DATA_wired.rightThighAngle)

                # TODO: Activate if used: Deactivated 17.03.2020 - Morten
                # self.myKneeAngleController.update(self.data.IMU_DATA_wired.leftKneeAngle, \
                #                                     self.data.IMU_DATA_wired.rightKneeAngle)

                self.myCrankAngleController.update(self.data.CyclingComputer_DATA.CrankAngle,
                                                   self.data.CyclingComputer_DATA.Cadence)

                # TODO: Activate Observer if used: Deactivated 30.01.2020 - Morten
                # self.myObserverController.update(self.data.IMU_DATA_wired.leftThighAngle, \
                #                                 self.data.IMU_DATA_wired.rightThighAngle, \
                #                                 self.data.IMU_DATA_wired.IMU_timestamp)


                ## Read Data from controllers
                self.data.Remote_Controller_DATA = self.myRemoteController.getData()
                self.data.Manual_Controller_DATA = self.myManualController.getData()
                self.data.ThighAngle_Controller_DATA = self.myThighAngleController.getData()
                self.data.KneeAngle_Controller_DATA = self.myKneeAngleController.getData()
                self.data.CrankAngle_Controller_DATA = self.myCrankAngleController.getData()
                self.data.Observer_Controller_DATA = self.myObserverController.getData()
                self.data.Biodex_Controller_DATA = self.myBiodexController.getData()


                # Cadence Information
                if(self.CONTROL_MODE == CONTROLLER_THIGHANGLE):
                    self.data.CyclingComputer_DATA.Cadence = self.data.ThighAngle_Controller_DATA.Cadence_L;

                ## Update Stimulator
                # Update BOOST
                self.myFESBox_Manager.updateBOOST(self.data.Button_BOOST)

                # Turn ON stimulation
                if(self.myGPIO_Manager.getButton_Emergency() == False):
                    if self.FLAG_RELAYBOX:
                        self.myFESBox_Manager.updateChannels(self.__UsedChannels, acknowledged = True)

                elif(self.myGPIO_Manager.getButton_Emergency() == True):
                    self.myFESBox_Manager.updateChannels([False, False, False, False, False, False, False, False], acknowledged = True)

                # Stimulation Amplitude - TODO: Make more general here
                #if self.CONTROL_MODE == CONTROLLER_TCP:
                       # self.myFESBox_Manager.updateAmplitude(self.myTCPController.getIPercentage())



                ## Update Channel-Switching Box
                if self.CONTROL_MODE == CONTROLLER_TCP:
                    self.data.activeController = 'R'

                    if not self.data.Button_Emergency == 1 or self.FLAG_Emergency_Button == False:
                        if self.FLAG_RELAYBOX:
                            self.myGPIO_Manager.updateChannels(self.myRemoteController.getActiveChannels(),
                                                               self.myRemoteController.getStimFlag())
                        else:
                            self.myFESBox_Manager.updateChannels(self.myRemoteController.getActiveChannels(), acknowledged=False)

                elif self.CONTROL_MODE == CONTROLLER_BIODEX:
                    self.data.activeController = 'B'

                    if not self.data.Button_Emergency == 1 or self.FLAG_Emergency_Button == False:
                        if self.FLAG_RELAYBOX:
                            self.myGPIO_Manager.updateChannels(self.myBiodexController.getActiveChannels(),
                                                               self.myBiodexController.getStimFlag())
                        else:
                            self.myFESBox_Manager.updateChannels(self.myBiodexController.getActiveChannels(), acknowledged=False)

                elif self.data.Switch_MAN_AUTO == 0:
                    self.data.activeController = 'M'

                    if not self.data.Button_Emergency == 1 or self.FLAG_Emergency_Button == False:
                        if self.FLAG_RELAYBOX:
                            self.myGPIO_Manager.updateChannels(self.myManualController.getActiveChannels())
                        else:
                            self.myFESBox_Manager.updateChannels(self.myManualController.getActiveChannels(), acknowledged=False)

                elif self.CONTROL_MODE == CONTROLLER_CRANKANGLE:
                    self.data.activeController = 'C'

                    if not self.data.Button_Emergency == 1 or self.FLAG_Emergency_Button == False:
                        if self.FLAG_RELAYBOX:
                            self.myGPIO_Manager.updateChannels(self.myCrankAngleController.getActiveChannels())
                        else:
                            self.myFESBox_Manager.updateChannels(self.myCrankAngleController.getActiveChannels(), acknowledged=False)

                elif self.CONTROL_MODE == CONTROLLER_KNEEANGLE:
                    self.data.activeController = 'K'

                    if not self.data.Button_Emergency == 1 or self.FLAG_Emergency_Button == False:
                        if self.FLAG_RELAYBOX:
                            self.myGPIO_Manager.updateChannels(self.myKneeAngleController.getActiveChannels())
                        else:
                            self.myFESBox_Manager.updateChannels(self.myKneeAngleController.getActiveChannels(), acknowledged=False)

                elif self.CONTROL_MODE == CONTROLLER_THIGHANGLE:
                    self.data.activeController = 'T'

                    if not self.data.Button_Emergency == 1 or self.FLAG_Emergency_Button == False:
                        if self.FLAG_RELAYBOX:
                            self.myGPIO_Manager.updateChannels(self.myThighAngleController.getActiveChannels())
                        else:
                            self.myFESBox_Manager.updateChannels(self.myThighAngleController.getActiveChannels(), acknowledged=False)

                elif self.CONTROL_MODE == CONTROLLER_OBSERVER:
                    self.data.activeController = 'O'

                    if not self.data.Button_Emergency == 1 or self.FLAG_Emergency_Button == False:
                        if self.FLAG_RELAYBOX:
                            self.myGPIO_Manager.updateChannels(self.myObserverController.getActiveChannels())
                        else:
                            self.myFESBox_Manager.updateChannels(self.myObserverController.getActiveChannels(), acknowledged=False)


                ## Write data to file
                if self.FLAG_LOG_DATA:
                    if not self.myDataLogger == None:
                        self.myDataLogger.logData(self.data)
                        self.data.comment = ""     # Reset comment to only be written once TODO: maybe timing problems

                ## Update system State
                self.updateSystemStatus()

                ## Send data to UDP-Client:
                if self.FLAG_UDP_SERVER:
                    if self.__UDP_Counter >= self.__UDP_Divider:
                        self.myUDP_Server.sendData(self.data.getJSON())
                        self.__UDP_Counter = 0
                    else:
                        self.__UDP_Counter += 1


                ## Signal watchdog that we are still running (if there is a watchdog)
                if self.Watchdog_Monitoring:
                    # If Keepalive signal needs to be refreshed, refresh.
                    if time.time() > self.Keepalive_timer + self.Keepalive_delay:
                        # Send the KEEPALIVE_SIGNAL to stdout. Flushing is imperative for some environments.
                        # print("sending keepalive")
                        sys.stdout.write("KEEPALIVE_SIGNAL\n")
                        sys.stdout.flush()
                        self.Keepalive_timer = time.time()

                if self.exit.isSet():
                    raise KeyboardInterrupt


                # A bit of sleep - Bonne nuit and stuff
                processing_time = time.time() - self.data.timestamp;
                if (processing_time < 0.010):
                    self.__my_sleep(0.010 - processing_time)




        except KeyboardInterrupt:

            print('\nUser requested Application STOP\n')
            self.__clean_exit()

        except Exception as error:
            print('\nException error: \n')
            traceback.print_exc()


            self.__clean_exit()


    # Loads the configuration from the defined File and adjusts IMUSEF
    def __loadConfig(self):

        file = open(self.__ConfigFile, "r")
        JSON_str = file.read();
        file.close()

        try:
            config = json.loads(JSON_str)
        except Exception as error:
            traceback.print_exc()
            return

        # Configure Module FLAGS
        module_config = config["ModuleConfig"]
        self.FLAG_RELAYBOX = module_config["FLAG_RELAYBOX"]
        self.FLAG_STIMULATOR = module_config["FLAG_STIMULATOR"]
        self.FLAG_CRANKANGLE_SENSOR_OPENDAQ = module_config["FLAG_CRANKANGLE_SENSOR_OPENDAQ"]
        self.FLAG_CRANKANGLE_SENSOR_IMU_FOX = module_config["FLAG_CRANKANGLE_SENSOR_IMU_FOX"]
        self.FLAG_IMUs = module_config["FLAG_IMUs"]
        self.FLAG_HEARTRATE_MONITOR = module_config["FLAG_HEARTRATE_MONITOR"]
        self.FLAG_POWERMETER_ROTOR = module_config["FLAG_POWERMETER_ROTOR"]
        self.FLAG_HOMETRAINER = module_config["FLAG_HOMETRAINER"]

        # Configure Button FLAGS
        button_config = config["ButtonConfig"]
        self.FLAG_Emergency_Button = button_config["FLAG_BUTTON_EMERGENCY"]
        self.FLAG_Left_Button = button_config["FLAG_BUTTON_LEFT"]
        self.FLAG_Right_Button = button_config["FLAG_BUTTON_RIGHT"]
        self.FLAG_Boost_Button = button_config["FLAG_BUTTON_BOOST"]
        self.FLAG_Man_Auto_Switch = button_config["FLAG_SWITCH_MAN_AUTO"]

        # Configure General Settings
        general_config = config["GeneralConfig"]
        self.CONTROL_MODE = general_config["ControlMode"]
        self.__Max_Cadence_Manual_Control = general_config["Max_Cadence_ManualMode"]
        self.myCyclingComputer.WheelCircumference = general_config["Circumference_RearWheel"]
        self.__MAC_Stimulator = general_config["MAC_Stimulator"]
        self.__ID_Rotor_Powermeter = general_config["ID_ROTOR"]
        self.__ID_HeartRateMonitor = general_config["ID_HeartRateMonitor"]

        # Stimulator Config
        self.myFESBox_Manager.configure(config["StimConfig"])

        # Controller Config
        self.myBiodexController.setConfig(config["Biodex_ControllerConfig"])
        self.myCrankAngleController.setConfig(config["CrankAngle_ControllerConfig"])
        self.myKneeAngleController.setConfig(config["KneeAngle_ControllerConfig"])
        self.myThighAngleController.setConfig(config["ThighAngle_ControllerConfig"])
        self.myObserverController.setConfig(config["Observer_ControllerConfig"])


    # Saves the current IMUSEF configuration to file
    def __saveConfig(self):

        module_config = {
            "@@@@@@@@FLAG_RELAYBOX": self.FLAG_RELAYBOX,
            "@@@@@@@FLAG_STIMULATOR": self.FLAG_STIMULATOR,
            "@@@@@@FLAG_CRANKANGLE_SENSOR_OPENDAQ": self.FLAG_CRANKANGLE_SENSOR_OPENDAQ,
            "@@@@@FLAG_CRANKANGLE_SENSOR_IMU_FOX": self.FLAG_CRANKANGLE_SENSOR_IMU_FOX,
            "@@@@FLAG_IMUs": self.FLAG_IMUs,
            "@@@FLAG_HEARTRATE_MONITOR": self.FLAG_HEARTRATE_MONITOR,
            "@@FLAG_POWERMETER_ROTOR": self.FLAG_POWERMETER_ROTOR,
            "@FLAG_HOMETRAINER": self.FLAG_HOMETRAINER
        }

        button_config = {
            "@@@@@FLAG_BUTTON_EMERGENCY": self.FLAG_Emergency_Button,
            "@@@@FLAG_BUTTON_LEFT": self.FLAG_Left_Button,
            "@@@FLAG_BUTTON_RIGHT": self.FLAG_Right_Button,
            "@@FLAG_BUTTON_BOOST": self.FLAG_Boost_Button,
            "@FLAG_SWITCH_MAN_AUTO": self.FLAG_Man_Auto_Switch
        }

        general_config = {
            "@@@@@@ControlMode" : self.CONTROL_MODE,
            "@@@@@Max_Cadence_ManualMode" : self.__Max_Cadence_Manual_Control,
            "@@@@Circumference_RearWheel": self.myCyclingComputer.WheelCircumference,
            "@@@MAC_Stimulator": self.__MAC_Stimulator,
            "@@ID_ROTOR": self.__ID_Rotor_Powermeter,
            "@ID_HeartRateMonitor": self.__ID_HeartRateMonitor
        }

        config = {
            "@@@@@@@@@ModuleConfig": module_config,
            "@@@@@@@@ButtonConfig": button_config,
            "@@@@@@@GeneralConfig": general_config,
            "@@@@@@StimConfig": self.__getSortedStimConfig(self.myFESBox_Manager.getStimConfig()),
            "@@@@@Biodex_ControllerConfig": self.__getSortedControllerConfig(self.myBiodexController.getConfig()),
            "@@@@CrankAngle_ControllerConfig": self.__getSortedControllerConfig(self.myCrankAngleController.getConfig()),
            "@@@KneeAngle_ControllerConfig": self.__getSortedControllerConfig(self.myKneeAngleController.getConfig()),
            "@@ThighAngle_ControllerConfig": self.__getSortedControllerConfig(self.myThighAngleController.getConfig()),
            "@Observer_ControllerConfig": self.__getSortedControllerConfig(self.myObserverController.getConfig())
        }

        config_JSON = json.dumps(config, sort_keys=True, indent=4, separators=(',', ': '))
        config_JSON = config_JSON.replace("@","")
        #print(config_JSON)

        file = open(self.__ConfigFile, "w")
        file.write(config_JSON);
        file.close()


    # Sets up the file for replay data simulation
    def __setup_simulate_from_file(self):
        self.input_simulation_file_path = self.input_sim_folder_name + self.input_sim_file_name
        self.input_simulation_file = open(self.input_simulation_file_path, "r+")
        print ("Input File opened: %s", self.input_sim_file_name)
        ## Reading header line
        header_line = self.input_simulation_file.readline()
        if header_line == '':
            print ("\nEmpty Input File : %s\n", self.input_simulation_file_path)
            self.FLAG_SIMULATE_FROM_FILE = False
            self.FLAG_SIMULATE_FROM_FILE_READY = False

        self.FLAG_SIMULATE_FROM_FILE_READY = True
        self.double_frequency_trick = False


    # Updates the values with the next sample from the replay data
    def __update_simulate_from_file(self):
        if not self.FLAG_SIMULATE_FROM_FILE_READY:
            return
        next_data_line = ''
        if self.FLAG_DOUBLE_FILE_FREQUENCY:
            if self.double_frequency_trick:
                self.next_data_line_sim = self.input_simulation_file.readline()
                next_line_splited = self.next_data_line_sim.split()
                previous_line_splited = self.previous_data_line_sim.split()

                # Oversampling linear estimation from next sample and previous one
                self.data.IMU_DATA_wired.IMU_timestamp = (float(next_line_splited[0]) - float(previous_line_splited[0]))/2 + float(previous_line_splited[0])
                self.data.IMU_DATA_wired.leftKneeAngle = (float(next_line_splited[1]) - float(previous_line_splited[1]))/2 + float(previous_line_splited[1])
                self.data.IMU_DATA_wired.rightKneeAngle = (float(next_line_splited[2]) - float(previous_line_splited[2]))/2 + float(previous_line_splited[2])
                self.data.IMU_DATA_wired.leftThighAngle = (float(next_line_splited[3]) - float(previous_line_splited[3]))/2 + float(previous_line_splited[3])
                self.data.IMU_DATA_wired.rightThighAngle = (float(next_line_splited[4]) - float(previous_line_splited[4]))/2 + float(previous_line_splited[4])
                self.data.IMU_DATA_wireless.CrankAngle = (float(next_line_splited[5]) - float(previous_line_splited[5]))/2 +float(previous_line_splited[5])

                self.double_frequency_trick = not self.double_frequency_trick
                return
            else:
                # First loop case
                if self.next_data_line_sim == '':
                    next_data_line = self.input_simulation_file.readline()
                    self.previous_data_line_sim = next_data_line
                else:
                    next_data_line = self.next_data_line_sim
                    self.previous_data_line_sim = next_data_line

            self.double_frequency_trick = not self.double_frequency_trick
        else:
            next_data_line = self.input_simulation_file.readline()

        if next_data_line == '':
            print ("\nEnd Of File : %s\n", self.input_sim_file_name)
            self.FLAG_SIMULATE_FROM_FILE_READY = False
            self.FLAG_SIMULATE_FROM_FILE = False
            self.stop_Datalogging.set()
            self.FLAG_LOG_DATA = False;
            self.double_frequency_trick = False
        else:
            splited_line = next_data_line.split()

            self.data.IMU_DATA_wired.IMU_timestamp = float(splited_line[0])
            self.data.IMU_DATA_wired.leftKneeAngle = float(splited_line[1])
            self.data.IMU_DATA_wired.rightKneeAngle = float(splited_line[2])
            self.data.IMU_DATA_wired.leftThighAngle = float(splited_line[3])
            self.data.IMU_DATA_wired.rightThighAngle = float(splited_line[4])
            self.data.IMU_DATA_wireless.CrankAngle = float(splited_line[5])


    # Sorts the ParameterNames by the use of @ - make sure to remove after creation of JSON-String
    def __getSortedStimConfig(self, _config):

        sorted_config = {
                "@@@@@@@@@F": _config["F"],
                "@@@@@@@@F_Boost": _config["F_Boost"],
                "@@@@@@@Monophasic": _config["Monophasic"],
                "@@@@@@PhW": _config["PhW"],
                "@@@@@PhW_Boost": _config["PhW_Boost"],
                "@@@@IPG": _config["IPG"],
                "@@@I_Max": _config["I_Max"],
                "@@RampUP": _config["RampUP"],
                "@RampDOWN": _config["RampDOWN"]
        }

        return sorted_config


    # Sorts the ParameterNames by the use of @ - make sure to remove after creation of JSON-String
    def __getSortedControllerConfig(self, _config):

        sorted_config = {
            "@@@@@Name": _config["Name"],
            "@@@@Min": _config["Min"],
            "@@@Max": _config["Max"],
            "@@Start": _config["Start"],
            "@Stop": _config["Stop"]
        }

        return sorted_config



    # Interprets and processes a new message received from the TCP-Client
    def __handleMessage(self, msg):

        ## Return Current stimulation configuration to the TCP-Client
        if msg.CMD == TCP_Message.CMD_GET_STIM_PARAMS:

            self.myGPIO_Manager.DoubleBeep()
            stim_params = self.myFESBox_Manager.getStimConfig()
            msg.buildMessage(TCP_Message.CMD_RE_GET_STIM_PARAMS, json.dumps(stim_params))
            self.myTCP_Server.sendData(msg.toString())

        ## Re-Configure FESBox
        elif msg.CMD == TCP_Message.CMD_SET_STIM_PARAMS:

            try:
                params = json.loads(msg.DATA)
            except Exception as error:
                traceback.print_exc()
                return

            # Inform that the message was received
            self.myGPIO_Manager.Beep()
            self.myRemoteController.update(I=0, CH_active=[False, False, False, False, False, False, False, False])
            update_OK = self.myFESBox_Manager.updateConfiguration(params)


            # Inform that the update failed
            if not update_OK:
                # Annoying beep
                self.myGPIO_Manager.Beep(0.5)

                # Inform the TCP-Client
                msg.buildMessage(TCP_Message.CMD_RE_SET_STIM_PARAMS, str(update_OK))
                self.myTCP_Server.sendData(msg.toString())

            # Saves new config to keep the values for the next start
            self.__saveConfig()

        ## Execute Test-Stimulation
        elif msg.CMD == TCP_Message.CMD_SET_TEST_STIMULATION:

            # Inform that the message was received
            self.myGPIO_Manager.Beep()

            # Update TCP-Controller
            self.myRemoteController.update(JSON=msg.DATA)

        ## Change Stimulation Intensity
        elif msg.CMD == TCP_Message.CMD_SET_STIMULATION_INTENSITY:

            # Inform that the message was received
            self.myGPIO_Manager.Beep()

            # Update TCP-Controller
            self.myFESBox_Manager.updateAmplitude(I = int(msg.DATA))

        # Return current Settings
        elif msg.CMD == TCP_Message.CMD_GET_SETTINGS:

            recording_active = False
            file_path = ""

            if not self.myDataLogger == None:
                recording_active = (self.myDataLogger.Status == 1)
                file_path = self.myDataLogger.file_path

            _settings = {
                "Controller": self.CONTROL_MODE,
                "Simulate_CrankAngle": self.FLAG_SIMULATE_CRANKANGLE,
                "Simulate_ThighAngles": self.FLAG_SIMULATE_THIGHANGLES,
                "Simulate_KneeAngles": self.FLAG_SIMULATE_KNEEANGLES,
                "Simulated_Cadence": int(self.__simulatedCadence),
                "DataLogging_Active": recording_active,
                "DataLogging_FilePath": file_path,
                "Biodex_Side": self.myBiodexController.getSide(),
                "FLAG_Button_Emergency":self.FLAG_Emergency_Button,
                "FLAG_Button_Left": self.FLAG_Left_Button,
                "FLAG_Button_Right":self.FLAG_Right_Button,
                "FLAG_Button_Boost": self.FLAG_Boost_Button,
                "FLAG_Switch_Man_Auto": self.FLAG_Man_Auto_Switch,
                "FLAG_Module_RelayBox": self.FLAG_RELAYBOX,
                "FLAG_Module_Stimulator": self.FLAG_STIMULATOR,
                "FLAG_Module_CrankAngle_Sensor_OpenDAQ": self.FLAG_CRANKANGLE_SENSOR_OPENDAQ,
                "FLAG_Module_CrankAngle_Sensor_IMU_FOX": self.FLAG_CRANKANGLE_SENSOR_IMU_FOX,
                "FLAG_Module_IMUs": self.FLAG_IMUs,
                "FLAG_Module_Heartrate_Monitor": self.FLAG_HEARTRATE_MONITOR,
                "FLAG_Module_PowerMeter_Rotor": self.FLAG_POWERMETER_ROTOR,
                "FLAG_Module_HomeTrainer": self.FLAG_HOMETRAINER,
                "WheelCircumference": (int)(self.myCyclingComputer.WheelCircumference*1000),
                "Max_Manual_Cadence": self.__Max_Cadence_Manual_Control,
                "MAC_Stimulator": self.__MAC_Stimulator,
                "ID_ROTOR": self.__ID_Rotor_Powermeter,
                "ID_HeartRateMonitor": self.__ID_HeartRateMonitor
            }

            msg.buildMessage(TCP_Message.CMD_RE_SETTINGS, json.dumps(_settings))
            self.myTCP_Server.sendData(msg.toString())

        # Return current Controller Mode
        elif msg.CMD == TCP_Message.CMD_SET_SETTINGS:

            try:
                _settings = json.loads(msg.DATA)
            except Exception as error:
                traceback.print_exc()
                return

            # Switch off TCP-Controller
            self.myRemoteController.update(I=0, CH_active=[False, False, False, False, False, False, False, False])

            controller = _settings["Controller"]

            if (    controller == CONTROLLER_NONE or
                    controller == CONTROLLER_TCP or
                    controller == CONTROLLER_CRANKANGLE or
                    controller == CONTROLLER_THIGHANGLE or
                    controller == CONTROLLER_OBSERVER or
                    controller == CONTROLLER_BIODEX):

                self.CONTROL_MODE = controller

            self.__simulatedCadence = _settings["Simulated_Cadence"]

            self.FLAG_SIMULATE_CRANKANGLE = _settings["Simulate_CrankAngle"]
            self.FLAG_SIMULATE_KNEEANGLES = _settings["Simulate_KneeAngles"]
            self.FLAG_SIMULATE_THIGHANGLES = _settings["Simulate_ThighAngles"]

            self.__sim_CrankAngleSpeed = (self.__simulatedCadence / 60.0) * 360.0
            self.__sim_w = 2 * np.pi * (self.__simulatedCadence / 60.0)

            # Button Flags
            self.FLAG_Emergency_Button = _settings["FLAG_Button_Emergency"]
            self.FLAG_Left_Button = _settings["FLAG_Button_Left"]
            self.FLAG_Right_Button = _settings["FLAG_Button_Right"]
            self.FLAG_Boost_Button = _settings["FLAG_Button_Boost"]
            self.FLAG_Man_Auto_Switch = _settings["FLAG_Switch_Man_Auto"]

            # Module Flags
            self.FLAG_RELAYBOX = _settings["FLAG_Module_RelayBox"]
            self.FLAG_STIMULATOR = _settings["FLAG_Module_Stimulator"]
            self.FLAG_CRANKANGLE_SENSOR_OPENDAQ = _settings["FLAG_Module_CrankAngle_Sensor_OpenDAQ"]
            self.FLAG_CRANKANGLE_SENSOR_IMU_FOX = _settings["FLAG_Module_CrankAngle_Sensor_IMU_FOX"]
            self.FLAG_IMUs = _settings["FLAG_Module_IMUs"]
            self.FLAG_HEARTRATE_MONITOR = _settings["FLAG_Module_Heartrate_Monitor"]
            self.FLAG_POWERMETER_ROTOR = _settings["FLAG_Module_PowerMeter_Rotor"]
            self.FLAG_HOMETRAINER = _settings["FLAG_Module_HomeTrainer"]

            # General Settings
            self.myCyclingComputer.WheelCircumference = _settings["WheelCircumference"]/1000.0
            self.__Max_Cadence_Manual_Control = _settings["Max_Manual_Cadence"]

            # Saves new config to keep the values for the next start
            self.__saveConfig()

            self.myGPIO_Manager.DoubleBeep()

        # Return the requested Controller configuration
        elif msg.CMD == TCP_Message.CMD_GET_CONTROLLER_PARAMS:

            self.myGPIO_Manager.DoubleBeep()
            config = {
                "CrankAngle_ControllerConfig": self.myCrankAngleController.getConfig(),
                "KneeAngle_ControllerConfig": self.myKneeAngleController.getConfig(),
                "ThighAngle_ControllerConfig": self.myThighAngleController.getConfig(),
                "Observer_ControllerConfig": self.myObserverController.getConfig(),
                "Biodex_ControllerConfig": self.myBiodexController.getConfig()
            }

            msg.buildMessage(TCP_Message.CMD_RE_CONTROLLER_PARAMS, json.dumps(config))
            self.myTCP_Server.sendData(msg.toString())

        # Sets new a Controller configuration
        elif msg.CMD == TCP_Message.CMD_SET_CONTROLLER_PARAMS:

            try:
                config = json.loads(msg.DATA)
            except Exception as error:
                traceback.print_exc()
                return

            self.myCrankAngleController.setConfig(config["CrankAngle_ControllerConfig"])
            self.myKneeAngleController.setConfig(config["KneeAngle_ControllerConfig"])
            self.myThighAngleController.setConfig(config["ThighAngle_ControllerConfig"])
            self.myObserverController.setConfig(config["Observer_ControllerConfig"])
            self.myBiodexController.setConfig(config["Biodex_ControllerConfig"])

            # Saves new config to keep the values for the next start
            self.__saveConfig()

            self.myGPIO_Manager.DoubleBeep()

        # Calibrates the system
        elif msg.CMD == TCP_Message.CMD_CALIBRATE_SYSTEM:
            self.myIMU_Manager_wireless.calibrate()
            self.myHometrainer.reCalibrate()
            self.myGPIO_Manager.DoubleBeep()

        # Stops IMUSEF
        elif msg.CMD == TCP_Message.CMD_STOP_SYSTEM:

            self.exit.set()
            self.myGPIO_Manager.DoubleBeep()

        # Resets Cycling Computer
        elif msg.CMD == TCP_Message.CMD_RESET_CYCLING_COMPUTER:

            self.myCyclingComputer.reset()
            self.myGPIO_Manager.DoubleBeep()

        # Start Recording
        elif msg.CMD == TCP_Message.CMD_START_RECORD:

            try:
                _filesettings = json.loads(msg.DATA)
            except Exception as error:
                traceback.print_exc()
                return

            self.myDataLogger = DataLogger(directory=_filesettings["Directory"],\
                                           filename=_filesettings["Filename"],\
                                           extension=_filesettings["Extension"],\
                                           timestamp=_filesettings["TimeStamp"])

            self.stop_Datalogging.clear()
            self.myDataLogger.start(self.stop_Datalogging)
            self.FLAG_LOG_DATA = True;

            msg.buildMessage(TCP_Message.CMD_RE_START_RECORD, self.myDataLogger.file_path)
            self.myTCP_Server.sendData(msg.toString())

            self.myGPIO_Manager.DoubleBeep()

        # Stop Recording
        elif msg.CMD == TCP_Message.CMD_STOP_RECORD:

            if not self.myDataLogger == None:
                self.stop_Datalogging.set()
                self.FLAG_LOG_DATA = False;

                msg.buildMessage(TCP_Message.CMD_RE_STOP_RECORD, self.myDataLogger.file_path)
                self.myTCP_Server.sendData(msg.toString())

                self.myDataLogger = None

                self.myGPIO_Manager.DoubleBeep()

        # Start Recording
        elif msg.CMD == TCP_Message.CMD_ADD_COMMENT:
            self.data.comment = msg.DATA;

        # Changes the Side of the BiodexController and returns the current State
        elif msg.CMD == TCP_Message.CMD_BIODEX_CHANGE_SIDE:
            if (msg.DATA == "LEFT"):
                self.myBiodexController.setSide(0)
            elif (msg.DATA == "RIGHT"):
                self.myBiodexController.setSide(1)

            self.myGPIO_Manager.DoubleBeep()

            recording_active = False
            file_path = ""

            if not self.myDataLogger == None:
                recording_active = (self.myDataLogger.Status == 1)
                file_path = self.myDataLogger.file_path

            _settings = {
                "Controller": self.CONTROL_MODE,
                "Simulate_CrankAngle": self.FLAG_SIMULATE_CRANKANGLE,
                "Simulate_ThighAngles": self.FLAG_SIMULATE_THIGHANGLES,
                "Simulate_KneeAngles": self.FLAG_SIMULATE_KNEEANGLES,
                "Simulated_Cadence": int(self.__simulatedCadence),
                "DataLogging_Active": recording_active,
                "DataLogging_FilePath": file_path,
                "Biodex_Side": self.myBiodexController.getSide()
            }

            msg.buildMessage(TCP_Message.CMD_RE_SETTINGS, json.dumps(_settings))
            self.myTCP_Server.sendData(msg.toString())

        # Calibrates the Biodex Controller to calculate the correct knee-angle
        elif msg.CMD == TCP_Message.CMD_BIODEX_CALIBRATE_KNEEANGLE:

            angle = 40
            try:
                angle = int(msg.DATA)
            except:
                angle = 40

            self.myBiodexController.calibrateKneeAngle(angle)
            self.myGPIO_Manager.DoubleBeep()


    # Updates the data Object with current information about the System
    def updateSystemStatus(self):

        # IMU´s
        if self.FLAG_IMUs == False:
            self.data.Status_IMUs = -1;
        elif self.FLAG_IMUs == True and self.myIMU_Manager.getIMUsReady() == False:
            self.data.Status_IMUs = -0;
        elif self.FLAG_IMUs == True and self.myIMU_Manager.getIMUsReady() == True:
            self.data.Status_IMUs = 1;

        # CrankAngle Sensor (IMU-Fox)
        if self.FLAG_CRANKANGLE_SENSOR_IMU_FOX:
            self.data.Status_CrankAngle_IMU_FOX = self.myIMU_Manager_wireless.getStatus()
        else:
            self.data.Status_CrankAngle_IMU_FOX = -1

        # CrankAngle Sensor (OpenDAQ)
        if self.FLAG_CRANKANGLE_SENSOR_OPENDAQ:
            self.data.Status_CrankAngle_OpenDAQ = self.myCrankAngleSensor.getStatus()
        else:
            self.data.Status_CrankAngle_OpenDAQ = -1

        # Stimulator
        if self.FLAG_STIMULATOR:
            self.data.Status_Stimulator = self.myFESBox_Manager.State
            self.data.StimIntensity = self.myFESBox_Manager.getStimulationIntensity()
        else:
            self.data.Status_Stimulator = -1

        # DataLogging
        if self.FLAG_LOG_DATA == False or self.myGPIO_Manager == None:
            self.data.Status_Datalogging = -1
        elif self.FLAG_LOG_DATA == True and not self.myDataLogger == None:
            self.data.Status_Datalogging = self.myDataLogger.Status

        # HeartRate Monitor
        if self.FLAG_HEARTRATE_MONITOR:
            self.data.Status_HeartRateMonitor = self.myANT_Manager.getState_HeartRateMonitor()
        else:
            self.data.Status_HeartRateMonitor = -1

        # PowerMeter
        if self.FLAG_POWERMETER_ROTOR:
            self.data.Status_PowerMeter = self.myANT_Manager.getState_PowerMeter()
        else:
            self.data.Status_PowerMeter = -1

        # HomeTrainer
        if self.FLAG_HOMETRAINER:
            self.data.Status_HomeTrainer = self.myHometrainer.getState()
        else:
            self.data.Status_HomeTrainer = -1




    def __my_sleep(self, duration):
        time2sleep = time.time() + duration - 0.0001;
        while time.time() < time2sleep:
            time.sleep(0.0001)

    # Tries to perform a clean exit - shuting down all modules individually
    def __clean_exit(self):

        #TODO: implement nicely

        # OpenAnt
        if self.FLAG_POWERMETER_ROTOR:
            self.myANT_Manager.clean_exit()

        # Switch off System LED
        self.myGPIO_Manager.setSystemLED(False)

        # Stop Modules
        self.exit.set()

        if not self.myDataLogger == None:
            self.stop_Datalogging.set()

        self.myTCP_Server.stop()

        if self.FLAG_IMUs:
            self.myIMU_Manager.stop()

        if self.FLAG_CRANKANGLE_SENSOR_IMU_FOX:
            self.myIMU_Manager_wireless.stop()

        if self.FLAG_STIMULATOR:
            self.myFESBox_Manager.disconnect()

        time.sleep(10)

        print('\n\n IMUSEF STOPPED - Au revoir!')
        sys.exit()



if __name__ == '__main__':
    Watchdog_Monitoring = False
    if len(sys.argv) >= 2:
        # print("Number of start arguments :", len(sys.argv))
        Watchdog_Monitoring = sys.argv[1]
        print("Watchdog_Monitoring flag changed : ", Watchdog_Monitoring)

    imusef = IMUSEF(Watchdog_Monitoring)
    imusef.run()

