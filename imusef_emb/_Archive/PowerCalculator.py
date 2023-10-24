


class PowerCalculator(object):

    def __init__(self, Segmentation):

        # Input
        self.__Torque = 0
        self.__Angle = 0

        # Settings

        # 0 ... Segmentation performed on given Angle (it is assumed that the angle is the crankangle)
        # 1 ... Segmentation every peak (for independent power calculation left or right leg)
        # 2 ... Segmentation every second peak (for calculation of total power of both legs)
        self.__Segmentation = Segmentation

        # Processing Variables
        self.__list_Timestamps = []
        self.__list_Torques = []


        # Output
        self.__Cadence = 0
        self.__Cadence_AVG = 0
        self.__Torque_AVG = 0
        self.__Power = 0
        self.__Power_AVG = 0


    # Adds the next data value for calculation
    def update(self, time, torque, angle):
        pass



