from CrankAngle_Controller_Data import CrankAngle_Controller_Data
import time

class CrankAngle_Controller(object):

    def __init__(self):

        # Input Parameters
        self.__CrankAngle = 0.0

        # Output Parameters
        self.__data = CrankAngle_Controller_Data()

        # Settings
        # CRANK ANGLE PATTERN USED BY J.P. DURING THE CYBATHLON 2016
        #self.__LQ_Start_Angle = 22
        #self.__LQ_Stop_Angle = 156
        #self.__RQ_Start_Angle = 202
        #self.__RQ_Stop_Angle = 337

        self.Min = 0
        self.Max = 360

        self.Start = [22, 202, 0, 0, 0, 0, 0, 0]
        self.Stop = [156, 337, 0, 0, 0, 0, 0, 0]


        # Limits
        self.__CADENCE_LIMIT_LOWER = 0  # [RPM]    # Minimal Cadence allowed in [RPM]
        self.__CADENCE_LIMIT_UPPER = 1000  # [RPM]    # Maximal Cadence allowed in [RPM]

        # Cadence
        self.__Cadence = None;

        self.activeChannels = [False, False, False, False, False, False, False, False]



    # Processes new Data and adjusts the controller
    def update(self, CrankAngle, Cadence):

        # Check Boundaries
        if CrankAngle < self.Min:
            CrankAngle = self.Min

        if CrankAngle > self.Max:
            CrankAngle = self.Max

        self.__CrankAngle = CrankAngle
        self.__Cadence = Cadence

        # Process the new Data
        self.__process()


    # Updates the stimulation channels
    def __process(self):

        if self.__CrankAngle < 0 or \
            self.__Cadence < self.__CADENCE_LIMIT_LOWER or \
            self.__Cadence > self.__CADENCE_LIMIT_UPPER:
            self.activeChannels = [False, False, False, False, False, False, False, False]
            return

        for ch in range(8):

                start = self.Start[ch]
                stop = self.Stop[ch]
                result = False

                if start == stop:
                    result = False

                elif start < stop:
                    if start <= self.__CrankAngle and self.__CrankAngle <= stop:
                        result = True
                    else:
                        result = False

                elif start > stop:
                    if not (stop < self.__CrankAngle and self.__CrankAngle < start):
                        result = True
                    else:
                        result = False

                self.activeChannels[ch] = result


    # Returns a CrankAngle_Controller_Data object containing the current state of the Controller
    def getData(self):

        self.__data.activeChannels = self.activeChannels[:]

        return self.__data

    # Returns the active Channels of the Controller
    def getActiveChannels(self):
        return self.activeChannels

    # Returns the current configuration
    def getConfig(self):
        data = {
            "Name": "CONTROLLER_CRANKANGLE",
            "Min": self.Min,
            "Max": self.Max,
            "Start": self.Start,
            "Stop": self.Stop
        }

        return data

    # Sets a new Configuration
    def setConfig(self, _config):

        self.Name = _config["Name"];
        self.Min = _config["Min"];
        self.Max = _config["Max"];
        self.Start = _config["Start"];
        self.Stop = _config["Stop"];