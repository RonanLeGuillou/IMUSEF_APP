
class Gonio_Controller_Data(object):

    def __init__(self):

        # Stimulation Flags
        self.LQ = False;
        self.RQ = False;
        self.LH = False;
        self.RH = False;

        self.L_peak_flexion = False;
        self.R_peak_flexion = False;
        self.L_peak_extension = False;
        self.R_peak_extension = False;

        self.NormalizedAngle_Left = 0.0
        self.NormalizedAngle_Right = 0.0

        self.Cadence_L = -1.0
        self.Cadence_R = -1.0

        self.activeChannels = [False, False, False, False, False, False, False, False]



