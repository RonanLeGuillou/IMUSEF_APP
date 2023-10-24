from Biodex_Controller_Data import Biodex_Controller_Data
import time


# Constants
LEFT = 0
RIGHT = 1

FLEXION = 0
EXTENSION = 1

class Biodex_Controller(object):



    def __init__(self):

        # Input Parameters
        self.__Biodex_Position = 0.0
        self.__Biodex_Speed_RAW = 0.0
        self.__Biodex_Speed = 0.0

        # Variables for Speed
        self.__lastTimeStamp = 0
        self.__lastBiodexPosition = 0
        self.OffSet_Speed = 0

        # Output Parameters
        self.__KneeExtensionAngle = 0
        self.__RepetitionCounter = 0
        self.activeChannels = [False, False, False, False, False, False, False, False]
        self.__data = Biodex_Controller_Data()
        self.__StimFlag = False


        # Settings
        self.__SIDE = LEFT

        self.__LEFT_MIN = 116         # [deg] of Biodex Position reflecting the minimal KneeExentsion Angle for LEFT LEG
        self.__LEFT_MAX = 206         # [deg] of Biodex Position reflecting the maximal KneeExentsion Angle for LEFT LEG

        self.__RIGHT_MIN = 216        # [deg] of Biodex Position reflecting the minimal KneeExentsion Angle for RIGHT LEG
        self.__RIGHT_MAX = 126        # [deg] of Biodex Position reflecting the minimal KneeExentsion Angle for RIGHT LEG

        self.__KneeAngleCalibrationValue = 0     # Value to be deduced to start of at a knee-Angle of 40 deg

        self.__KNEE_EXTENSION_ANGLE_MIN = 40
        self.__KNEE_EXTENSION_ANGLE_MAX = 130

        self.__MIN_SPEED_FOR_STIMULATION = 10 #[deg/s] Prevents stimulation when the Biodex is not moving

        self.Min = 25
        self.Max = 180

        self.Start = [self.Min, self.Min, self.Min, self.Min, self.Min, self.Min, self.Min, self.Min]
        self.Stop = [self.Min, self.Min, self.Min, self.Min, self.Min, self.Min, self.Min, self.Min]



        # Boundaries
        self.__Stim_Min = self.Min
        self.__Stim_Max = self.Min
        self.__Direction = 1        # 1... Extension; 0 ... Flexion





    # Processes new Data and adjusts the controller
    def update(self, Biodex_Position, Biodex_Speed = None):

        self.__Biodex_Position = Biodex_Position

        # Calculate Speed
        if(Biodex_Speed == None):

            # Init
            if (self.__lastTimeStamp == 0):
                self.__lastTimeStamp = time.time()
                self.__lastBiodexPosition = Biodex_Position
                self.__Biodex_Speed = 0

            # Calculate
            else:
                now = time.time()
                delta_t = now - self.__lastTimeStamp

                # Update value every 100ms to make it more stable
                if (delta_t >= 0.05):
                    self.__lastTimeStamp = now

                    delta_pos = Biodex_Position - self.__lastBiodexPosition
                    self.__lastBiodexPosition = Biodex_Position

                    self.__Biodex_Speed = delta_pos / delta_t

        # Just take given value
        else:
            self.__Biodex_Speed_RAW = Biodex_Speed

        self.__Biodex_Speed = self.__Biodex_Speed_RAW -self.OffSet_Speed

        if self.__Biodex_Speed < 0:
            self.__Biodex_Speed = -self.__Biodex_Speed

        if(self.__SIDE == LEFT):
            min = self.__LEFT_MIN
            max = self.__LEFT_MAX
        else:
            min = self.__RIGHT_MIN
            max = self.__RIGHT_MAX


        # Calculate Knee Extension Angle
        relativeAngle = (self.__Biodex_Position - min) / (max - min)

        self.__KneeExtensionAngle = relativeAngle * (self.__KNEE_EXTENSION_ANGLE_MAX - self.__KNEE_EXTENSION_ANGLE_MIN) + self.__KNEE_EXTENSION_ANGLE_MIN
        self.__KneeExtensionAngle = self.__KneeExtensionAngle - self.__KneeAngleCalibrationValue

        # Process the new Data
        self.__process()


    # Updates the stimulation channels
    def __process(self):

        # Extension phase
        if self.__KneeExtensionAngle < self.__Stim_Min:
            self.__Direction = EXTENSION

        # Flexion phase
        elif self.__KneeExtensionAngle > self.__Stim_Max:

            if(self.__Direction == EXTENSION):
                self.__RepetitionCounter += 1
                self.__Direction = FLEXION


        # Stimulate only every second repetition
        SecondRep = (self.__RepetitionCounter % 2) == 1



        for ch in range(8):

            start = self.Start[ch]
            stop = self.Stop[ch]
            result = False;

            if start == stop:
                result = False;

            elif start < stop:
                if start <= self.__KneeExtensionAngle and self.__KneeExtensionAngle <= stop:
                    result = True
                else:
                    result = False

            elif start > stop:
                if not (stop < self.__KneeExtensionAngle and self.__KneeExtensionAngle < start):
                    result = True
                else:
                    result = False

            self.activeChannels[ch] = result

        if (self.activeChannels[0] or
            self.activeChannels[1] or
            self.activeChannels[2] or
            self.activeChannels[3] or
            self.activeChannels[4] or
            self.activeChannels[5] or
            self.activeChannels[6] or
            self.activeChannels[7]):
            self.__StimFlag = True
        else:
            self.__StimFlag = False

        if(self.__Direction == FLEXION or\
          self.__Biodex_Speed < self.__MIN_SPEED_FOR_STIMULATION ):
            self.__StimFlag = False

          #

        # Conditions where NOT to stimulate
        if self.__KneeExtensionAngle < self.Min or\
           self.__KneeExtensionAngle > self.Max or \
           self.__Direction == FLEXION or \
           self.__Biodex_Speed < self.__MIN_SPEED_FOR_STIMULATION or \
         SecondRep:
            self.activeChannels = [False, False, False, False, False, False, False, False]
            return

    # Sets the side of the leg investigated
    def setSide(self, Side):
        self.__SIDE = Side

    # Returns the Side of the leg which is currently considered for the kneeangle
    def getSide(self):
        return self.__SIDE

    # Sets the KneeAngle to its intended starting point
    def calibrateKneeAngle(self, Angle):

        self.OffSet_Speed = self.__Biodex_Speed_RAW

        if (self.__SIDE == LEFT):
            min = self.__LEFT_MIN
            max = self.__LEFT_MAX
        else:
            min = self.__RIGHT_MIN
            max = self.__RIGHT_MAX

        # Calculate Knee Extension Angle
        relativeAngle = (self.__Biodex_Position - min) / (max - min)

        temp__KneeExtensionAngle = relativeAngle * (self.__KNEE_EXTENSION_ANGLE_MAX - self.__KNEE_EXTENSION_ANGLE_MIN) + self.__KNEE_EXTENSION_ANGLE_MIN

        self.__KneeAngleCalibrationValue = temp__KneeExtensionAngle - Angle


    # Returns a CrankAngle_Controller_Data object containing the current state of the Controller
    def getData(self):

        self.__data.activeChannels = self.activeChannels[:]
        self.__data.BiodexPosition = self.__Biodex_Position
        self.__data.KneeExtensionAngle = self.__KneeExtensionAngle
        self.__data.SIDE = self.__SIDE
        self.__data.BiodexSpeed = self.__Biodex_Speed
        self.__data.StimFlag = self.__StimFlag

        return self.__data

    # Returns the active Channels of the Controller
    def getActiveChannels(self):
        return self.activeChannels

    # Returns the active Channels of the Controller
    def getStimFlag(self):
        return self.__StimFlag

    # Returns the current configuration
    def getConfig(self):
        data = {
            "Name": "CONTROLLER_BIODEX",
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

        self.__Stim_Min = self.Max
        self.__Stim_Max = self.Min

        for i in range(8):

            # Ignore equal channels
            if self.Start[i] == self.Stop[i]:
                pass
            else:
                if(self.Start[i]<self.__Stim_Min):
                    self.__Stim_Min = self.Start[i]

                if (self.Stop[i] > self.__Stim_Max):
                    self.__Stim_Max = self.Stop[i]

