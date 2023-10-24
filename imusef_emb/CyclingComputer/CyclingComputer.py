from CyclingComputer_Data import CyclingComputer_Data
import time

class CyclingComputer(object):

    def __init__(self):

        # Constants
        self.Min = 0.0
        self.Max = 360.0

        # Input Parameters
        self.__CrankAngle = 0.0

        # Output Parameters
        self.__data = CyclingComputer_Data()

        ## Variables
        self.__Timestamp = 0.0

        # Cycle Detection
        self.__NewCycle = False     # Defines when a new cycle has started
        self.__JUMP_Threshold = 50

        # Cadence
        self.__Cadence = 0.0
        self.__Cadence_Filter = []
        self.__Cadence_Filter_Size = 100

        # Integrated Cycling Power
        self.__Power_integral = 0.0
        self.__accumulatedTime = 0.0
        self.__PowerTimeOut = 2.0       # Get a average Power every cycle or every 2 s
        self.__Power_AVG = 0.0

        # Distance
        self.__Distance = 0.0       # [m]

        # Speed
        self.__Speed_Max = 30       # [km/h]
        self.__Speed = 0.0          # [km/h]
        self.__SpeedPeriod = 1000   # [s]
        self.__lastSpeedTimestamp = 0.0
        self.WheelCircumference = 2.099  #[m]  # ICE: 2.03m CAT: 2.099m




    # Processes new Data and adjusts the controller
    def update(self, new_TimeStamp, CrankAngle, Power, Speed_TimeStamp):

        # Boundary Check
        if CrankAngle < self.Min:
            CrankAngle = self.Min

        if CrankAngle > self.Max:
            CrankAngle = self.Max


        # Save old Values
        OLD_CrankAngle = self.__CrankAngle
        OLD_TimeStamp = self.__Timestamp


        # Update Values
        self.__CrankAngle = CrankAngle
        self.__Timestamp = new_TimeStamp

        # Calculate Cadence
        delta_CrankAngle = self.__CrankAngle - OLD_CrankAngle
        delta_t = self.__Timestamp - OLD_TimeStamp
        t_Cadence = (delta_CrankAngle / 360.0)/ (delta_t /60)


        # Calculate Cadence
        if OLD_TimeStamp > 0:

            # Calculate Power integral
            self.__Power_integral += Power * delta_t
            self.__accumulatedTime += delta_t


            # New Cycle started
            if (delta_CrankAngle < -self.__JUMP_Threshold) or (delta_CrankAngle > self.__JUMP_Threshold):
               self.__NewCycle = True

            # Filter and Update Cadence
            else:
                if len(self.__Cadence_Filter) < self.__Cadence_Filter_Size:
                    self.__Cadence_Filter.append(t_Cadence)
                    self.__Cadence = 0.0
                else:
                    self.__Cadence_Filter.append(t_Cadence)
                    self.__Cadence_Filter.pop(0)
                    self.__Cadence = sum(self.__Cadence_Filter) / len(self.__Cadence_Filter)

                self.__NewCycle = False

            # Reset Power calculation due to new cycle or Timeout
            if self.__NewCycle or self.__accumulatedTime > self.__PowerTimeOut:

                self.__Power_AVG = self.__Power_integral / self.__accumulatedTime
                self.__Power_integral = 0.0
                self.__accumulatedTime = 0.0



        ## Calculate Speed

        # init
        if self.__lastSpeedTimestamp == 0.0 and Speed_TimeStamp > 0.0:
            self.__lastSpeedTimestamp = Speed_TimeStamp

        # calculate
        else:

            # New Speed-Flag: Speed Update
            if not self.__lastSpeedTimestamp == Speed_TimeStamp:

                self.__Distance = self.__Distance + self.WheelCircumference;

                self.__SpeedPeriod = Speed_TimeStamp - self.__lastSpeedTimestamp;
                self.Speed = 3.6 * (self.WheelCircumference / self.__SpeedPeriod)
                self.__lastSpeedTimestamp = Speed_TimeStamp

            # Nothing new
            else:
                diff = new_TimeStamp - self.__lastSpeedTimestamp;

                # Getting Slower
                if  diff > self.__SpeedPeriod:
                    self.Speed = 3.6 * (self.WheelCircumference / diff)

                if diff > 10:
                    self.Speed = 0.0


    # Resets the Cycling Computer
    def reset(self):
        self.__Distance = 0.0


    # Returns a CyclingComputer_Data
    def getData(self):

        self.__data.Power_AVG = self.__Power_AVG
        self.__data.Cadence = self.__Cadence
        self.__data.NewCycle = self.__NewCycle
        self.__data.Speed = self.Speed
        self.__data.Distance = self.__Distance

        return self.__data

