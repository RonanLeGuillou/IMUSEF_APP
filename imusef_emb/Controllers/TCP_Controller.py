import json, time
from CrankAngle_Controller_Data import CrankAngle_Controller_Data

class TCP_Controller(object):

    def __init__(self):

        # Input Parameters
        self.__I_percentage = 0

        self.BurstDuration = -1
        self.StimulationStarted = 0

        self.__StimFlag = False

        # Output Parameters
        self.__data = CrankAngle_Controller_Data()



        # Output Parameters
        self.__activeChannels = [False, False, False, False, False, False, False, False]


    # Processes new Data and adjusts the controller
    def update(self, JSON = None, I = None, CH_active = None ):

        if(not JSON == None ):
            data = json.loads(JSON)
            self.__I_percentage = data["I_percent"]
            self.__activeChannels = data["CH_Active"]
            self.BurstDuration = data["Burst_Duration"]
            self.StimulationStarted = time.time()

        elif (I is not None and CH_active is not None):
            self.__I_percentage = I
            self.__activeChannels = CH_active

        self.process()


    # Processes the Data and updates the stimulation channels
    def process(self):

        # Testburst - Mode
        if (self.BurstDuration > 0):

            timeStimulated = (time.time() - self.StimulationStarted)*1000

            # Switch off TestBurst
            if(self.BurstDuration <= timeStimulated):
                self.__I_percentage = 0.0
                self.__activeChannels = [False, False, False, False, False, False, False, False]
                self.BurstDuration = -1
                self.StimulationStarted = 0

        if (self.__activeChannels[0] or
                self.__activeChannels[1] or
                self.__activeChannels[2] or
                self.__activeChannels[3] or
                self.__activeChannels[4] or
                self.__activeChannels[5] or
                self.__activeChannels[6] or
                self.__activeChannels[7]):
            self.__StimFlag = True
        else:
            self.__StimFlag = False

    # Returns Controller_Data containing the current state of the Controller
    def getData(self):

        self.__data.activeChannels = self.__activeChannels[:]

        return self.__data

    # Returns the active Channels of the Controller
    def getStimFlag(self):
        return self.__StimFlag

    # Returns an array of the active Channels
    def getActiveChannels(self):
        return self.__activeChannels

    # Sets the active Channels of the TCP Controller
    def setActiveChannels(self, active_channels):
        self.__activeChannels = active_channels

    # Returns the global relative Stimulation Intensity
    def getIPercentage(self):
        return self.__I_percentage

    # Sets the general relative Stimulation Current for the TCP-Controller
    def setIPercentage(self, I):
        self.__I_percentage = I