import numpy as np
from Gonio_Controller_Data import Gonio_Controller_Data

class Gonio_KneeAngle_Controller(object):

    def __init__(self):

        # Input Parameters
        self.r_t_angle = 0.0
        self.l_t_angle = 0.0

        # Output Parameters
        self.LQ = False
        self.RQ = False

        self.LH = False
        self.RH = False

        self.data = Gonio_Controller_Data()

        # Settings
        self.l_delay = 5
        self.r_delay = 5

        # Processing Variables
        self.last_l_k_angle = 0.0
        self.last_r_k_angle = 0.0

        self.l_flexed = False
        self.r_flexed = False

        self.l_extended = False
        self.r_extended = False

        self.r_k_state = 0
        self.l_k_state = 0

        self.min_range_of_motion = 5
        self.min_range_between_pke_and_pkf = 20

        # Peak detetction
        self.l_pk_e = False
        self.r_pk_e = False
        self.l_pk_f = False
        self.r_pk_f = False

        self.log_l_pk_e = False
        self.log_r_pk_e = False
        self.log_l_pk_f = False
        self.log_r_pk_f = False

        self.last_l_pk_f = []
        self.last_r_pk_f = []
        self.last_l_pk_e = []
        self.last_r_pk_e = []

        # Configuration
        self.Min = 0
        self.Max = 180

        self.Start = [0, 0, 0, 0, 0, 0, 0, 0]
        self.Stop = [0, 0, 0, 0, 0, 0, 0, 0]

        self.activeChannels = [False, False, False, False, False, False, False, False]



    # Processes new Data and adjusts the controller
    def update(self, leftKneeAngle, rightKneeAngle):

        self.l_k_angle = leftKneeAngle
        self.r_k_angle = rightKneeAngle

        # Reset peak logs
        if self.log_l_pk_f or self.log_r_pk_f or self.log_l_pk_e or self.log_r_pk_e:
            self.log_l_pk_f = False
            self.log_r_pk_f = False
            self.log_l_pk_e = False
            self.log_r_pk_e = False


        # RIGHT Flexion or Extension detection
        diff_r = self.r_k_angle - self.last_r_k_angle
        if np.abs(diff_r) >= self.min_range_of_motion:
            if np.sign(diff_r) == 1:
                self.r_k_state = 1
            else:
                self.r_k_state = -1
            self.last_r_k_angle = self.r_k_angle

        # LEFT Flexion or Extension detection
        diff_l = self.l_k_angle - self.last_l_k_angle
        if np.abs(diff_l) >= self.min_range_of_motion:
            if np.sign(diff_l) == 1:
                self.l_k_state = 1
            else:
                self.l_k_state = -1
            self.last_l_k_angle = self.l_k_angle

        # Right Knee PKF and PKE
        if self.r_k_state == -1:  # FLEXION
            if self.r_extended:  # FLEXION AFTER EXTENSION
                if (not self.last_r_pk_f) or (
                        abs(self.last_r_pk_f - self.r_k_angle) >= self.min_range_between_pke_and_pkf):
                    self.r_pk_e = True
                    self.log_r_pk_e = True
                    if not self.last_r_pk_e:  # first time
                        print(' R PEAK EXTENSION: ' + str(self.r_k_angle))
                        self.r_pk_e = False
                    self.last_r_pk_e = self.r_k_angle
                self.r_extended = False
            self.r_flexed = True
        elif self.r_k_state == 1:  # EXTENSION
            if self.r_flexed:  # EXTENSION AFTER FLEXION
                if (not self.last_r_pk_e) or (
                        abs(self.last_r_pk_e - self.r_k_angle) >= self.min_range_between_pke_and_pkf):
                    self.r_pk_f = True
                    self.log_r_pk_f = True
                    if not self.last_r_pk_f:  # first time
                        print(' R PEAK FLEXION: ' + str(self.r_k_angle))
                        self.r_pk_f = False
                    self.last_r_pk_f = self.r_k_angle
                self.r_flexed = False
            self.r_extended = True

        # Left Knee PKF and PKE
        if self.l_k_state == -1:  # FLEXION
            if self.l_extended:  # FLEXION AFTER EXTENSION
                if (not self.last_l_pk_f) or (
                        abs(self.last_l_pk_f - self.l_k_angle) >= self.min_range_between_pke_and_pkf):
                    self.l_pk_e = True
                    self.log_l_pk_e = True
                    if not self.last_l_pk_e:  # first time
                        print(' L PEAK EXTENSION: ' + str(self.l_k_angle))
                        self.l_pk_e = False
                    self.last_l_pk_e = self.l_k_angle
                self.l_extended = False
            self.l_flexed = True

        elif self.l_k_state == 1:  # EXTENSION
            if self.l_flexed:  # EXTENSION AFTER FLEXION
                if (not self.last_l_pk_e) or (
                        abs(self.last_l_pk_e - self.l_k_angle) >= self.min_range_between_pke_and_pkf):
                    self.l_pk_f = True
                    self.log_l_pk_f = True
                    if not self.last_l_pk_f:  # first time
                        print(' L PEAK FLEXION: ' + str(self.l_k_angle))
                        self.l_pk_f = False
                    self.last_l_pk_f = self.l_k_angle
                self.l_flexed = False
            self.l_extended = True

        # Process the new Data
        self.__process()


    # Updates the stimulation channels
    def __process(self):
        # TODO: Implement
        pass

    # Returns a Gonio_Controller_Data object containing the current state of the Controller
    def getData(self):
        self.data.LQ = self.LQ
        self.data.RQ = self.RQ
        self.data.LH = self.LH
        self.data.RH = self.RH

        # self.data.L_peak_flexion = self.l_pk_f
        # self.data.R_peak_flexion = self.r_pk_f
        #
        # self.data.L_peak_extension = self.l_pk_e
        # self.data.R_peak_extension = self.r_pk_e

        self.data.L_peak_flexion = self.log_l_pk_f
        self.data.R_peak_flexion = self.log_r_pk_f

        self.data.L_peak_extension = self.log_l_pk_e
        self.data.R_peak_extension = self.log_r_pk_e

        return self.data

    # Returns the active Channels
    def getActiveChannels(self):
        return self.activeChannels

    # Returns the current configuration
    def getConfig(self):
        data = {
            "Name": "CONTROLLER_KNEEANGLE",
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