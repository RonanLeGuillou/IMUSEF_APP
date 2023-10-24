import json
import time
from IMU.imu_wired.IMU_Data_wired import IMU_Data_wired
from IMU.imu_wireless.IMU_Manager_wireless import IMU_Data_wireless
from Controllers.Gonio_Controller_Data import Gonio_Controller_Data
from Controllers.CrankAngle_Controller import CrankAngle_Controller_Data
from Controllers.Observer_Controller_Data import Observer_Controller_Data
from Controllers.Biodex_Controller_Data import Biodex_Controller_Data
from HomeTrainer.Hometrainer_Data import Hometrainer_Data
from CyclingComputer.CyclingComputer_Data import CyclingComputer_Data
from openANT.Powermeter_Data import Powermeter_Data


class IMUSEF_Data(object):

    def __init__(self):


        # Timestamp
        self.timestamp = 0
        self.__t0 = time.time()

        # System Data
        self.LoopTime = 0

        # Comment
        self.comment = "";

        # Physiological Data
        self.HeartRate = 0.0;

        # IMU Data
        self.IMU_DATA_wired = IMU_Data_wired()
        self.IMU_DATA_wireless = IMU_Data_wireless()

        # Controller Data
        self.activeController = 'N';    # 'N' ... None
                                        # 'R' ... Remote Contol (TCP Controller)
                                        # 'B' ... Biodex Controller
                                        # 'M' ... Manual Controller
                                        # 'C' ... CrankAngle Controller
                                        # 'T' ... ThighAngle Controller
                                        # 'K' ... KneeAngle Controller
                                        # 'G' ... Gonio Controller Benoit
                                        # 'O' ... Observer Controller

        self.Remote_Controller_DATA = CrankAngle_Controller_Data()
        self.Manual_Controller_DATA = CrankAngle_Controller_Data()
        self.ThighAngle_Controller_DATA = Gonio_Controller_Data()
        self.KneeAngle_Controller_DATA = Gonio_Controller_Data()
        self.Observer_Controller_DATA = Observer_Controller_Data()
        self.CrankAngle_Controller_DATA = CrankAngle_Controller_Data()
        self.Biodex_Controller_DATA = Biodex_Controller_Data()

        self.PowerMeter_DATA = Powermeter_Data()

        # Module Status
        # -2 ... ERROR
        # -1 ... Module not activated
        #  0 ... Module not ready
        #  1 ... Module ready

        self.Status_Stimulator = -1

        self.Status_IMUs = -1
        self.Status_CrankAngle_OpenDAQ = -1
        self.Status_HomeTrainer = -1
        self.Status_PowerMeter = -1
        self.Status_HeartRateMonitor = -1
        self.Status_Datalogging = -1
        self.Status_CrankAngle_IMU_FOX = -1  # Currently not in use


        # Stimulator Data
        self.StimIntensity = 0.0;

        # Buttons
        # -1 ... Button deactivated
        #  1 ... Button not pressed
        #  0 ... Button pressed
        self.Button_Emergency = -1
        # -1 ... Button deactivated
        #  0 ... Button not pressed
        #  1 ... Button pressed
        self.Button_LEFT = -1
        self.Button_RIGHT = -1
        self.Button_BOOST = -1
        self.Switch_MAN_AUTO = -1


        self.Hometrainer_DATA = Hometrainer_Data()

        self.CyclingComputer_DATA = CyclingComputer_Data()



    # Returns a JSON-String representing the current IMUSEF_Data Object
    def getJSON(self):

        data = {

                # TimeStamp
                "T": '%.5f' % (self.timestamp - self.__t0),

                # ThighAngle Data
                "TA1": '%.1f' % self.IMU_DATA_wired.leftThighAngle,
                "TA2": '%.1f' % self.IMU_DATA_wired.rightThighAngle,
                "TA3": '%.1f' % self.ThighAngle_Controller_DATA.NormalizedAngle_Left,
                "TA4": '%.1f' % self.ThighAngle_Controller_DATA.NormalizedAngle_Right,
                "TA5":          self.boolArray2string(self.ThighAngle_Controller_DATA.activeChannels),

                # KneeAngle Data
                "KA1": '%.1f' % self.IMU_DATA_wired.leftKneeAngle,
                "KA2": '%.1f' % self.IMU_DATA_wired.rightKneeAngle,
                "KA3": '%.1f' % self.KneeAngle_Controller_DATA.NormalizedAngle_Left,
                "KA4": '%.1f' % self.KneeAngle_Controller_DATA.NormalizedAngle_Right,
                "KA5":          self.boolArray2string(self.KneeAngle_Controller_DATA.activeChannels),

                # CrankAngle Data
                "CA1": '%.1f' % self.CyclingComputer_DATA.CrankAngle,
                "CA2": '%.1f' % self.PowerMeter_DATA.CrankAngle,
                "CA3": '%.1f' % self.IMU_DATA_wireless.CrankAngle,
                "CA4":          self.boolArray2string(self.CrankAngle_Controller_DATA.activeChannels),

                # Observer Data: TODO - Currently inactive
                "OB1": '%.1f' % self.Observer_Controller_DATA.Phase,
                "OB2":          self.boolArray2string(self.Observer_Controller_DATA.activeChannels),

                # PowerMeter Data
                "PM1": '%.1f' % self.PowerMeter_DATA.DataRate_F1,
                "PM2": '%.1f' % self.PowerMeter_DATA.DataRate_F2,
                "PM3": '%.1f' % self.PowerMeter_DATA.DataRate_F3,
                "PM4": '%.1f' % (self.PowerMeter_DATA.Cadence_AVG),
                "PM5": '%.1f' % (self.PowerMeter_DATA.Torque_Total),
                "PM6": '%.1f' % (self.PowerMeter_DATA.Power_Total),
                "PM7": '%.1f' % (self.PowerMeter_DATA.Power_Left),
                "PM8": '%.1f' % (self.PowerMeter_DATA.Power_Right),

                # HeartRate Data
                "HR": '%.3f' % self.HeartRate,

                # HomeTrainer Data
                "HT1": '%.3f' % self.Hometrainer_DATA.Torque,
                "HT2": '%.1f' % self.Hometrainer_DATA.Power,
                "HT3": '%.1f' % self.Hometrainer_DATA.Power_AVG,
                "HT4": '%.1f' % self.Hometrainer_DATA.Speed,

                # CyclingComputer Data
                "CC1": '%.1f' % self.CyclingComputer_DATA.Speed,
                "CC2": '%.1f' % self.CyclingComputer_DATA.Distance,
                "CC3": '%.1f' % self.CyclingComputer_DATA.Cadence,

                # Status Variables
                "S1": self.Status_Stimulator,
                "S2": self.Status_IMUs,
                "S3": self.Status_CrankAngle_OpenDAQ,
                "S4": self.Status_HomeTrainer,
                "S5": self.Status_PowerMeter,
                "S6": self.Status_HeartRateMonitor,
                "S7": self.Status_Datalogging,
                "S8": self.Status_CrankAngle_IMU_FOX,

                # Button States
                "B1": self.Button_Emergency,
                "B2": self.Button_LEFT,
                "B3": self.Button_RIGHT,
                "B4": self.Button_BOOST,
                "B5": self.Switch_MAN_AUTO,

                # Stimulator Data
                "ST1":                    self.StimIntensity,

                # System Varibles
                "SY1":  '%.1f' %    (self.LoopTime*1000),
                "SY2":  self.StimIntensity
        }

        data_str = json.dumps(data)

        return data_str


    # Returns a String for a boolean array
    def boolArray2string(self, activeChannels):

        result_string = ''
        for channel_bool in activeChannels:
            result_string = result_string + str(int(channel_bool))

        return result_string


if __name__ == '__main__':

    DATA = IMUSEF_Data();
    print(str(DATA.IMU_DATA_wireless.CrankAngle))

    DATA.IMU_DATA_wireless.CrankAngle = 10;

    print(str(DATA.IMU_DATA_wireless.CrankAngle))