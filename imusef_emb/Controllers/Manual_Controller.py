from CrankAngle_Controller_Data import CrankAngle_Controller_Data
import time

class Manual_Controller(object):

    def __init__(self):

        # Input Parameters
        self.__CrankAngle = 0.0

        # Output Parameters
        self.__data = CrankAngle_Controller_Data()

        self.__BT_Left = False
        self.__BT_Right = False

        self.__KneeAngle_Left = -1
        self.__KneeAngle_Right = -1


        self.activeChannels = [False, False, False, False, False, False, False, False]



    # Processes new Data and adjusts the controller
    def update(self, Button_Left, Button_Right, KneeAngle_Left = -1, KneeAngle_Right = -1):

        # Button status
        if Button_Left == 1:
            self.__BT_Left = True
        else:
            self.__BT_Left = False

        if Button_Right == 1:
            self.__BT_Right = True
        else:
            self.__BT_Right = False

        # KneeAngles
        self.__KneeAngle_Left = KneeAngle_Left
        self.__KneeAngle_Right = KneeAngle_Right

        # Process the new Data
        self.__process()


    # Updates the stimulation channels
    def __process(self):

        # Left extension Right flexion
        if self.__BT_Left and  not self.__BT_Right:
            self.activeChannels = [True, False, False, False, False, False, False, False]

        # Left Flexion and Right Extension
        elif not self.__BT_Left and  self.__BT_Right:
            self.activeChannels = [False, True, False, False, False, False, False, False]

        else:
            self.activeChannels = [False, False, False, False, False, False, False, False]



    # Returns Controller_Data containing the current state of the Controller
    def getData(self):

        self.__data.activeChannels = self.activeChannels[:]

        return self.__data

    # Returns the active Channels of the Controller
    def getActiveChannels(self):
        return self.activeChannels
