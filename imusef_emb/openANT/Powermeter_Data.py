
class Powermeter_Data(object):

    def __init__(self):

        self.BatteryStatus = -1
        self.DataRate_F1 = 0
        self.DataRate_F2 = 0
        self.DataRate_F3 = 0

        self.OCA = 0.0

        self.Force_left = 0.0
        self.Force_right = 0.0
        self.Force_total = 0.0

        self.Torque_left = 0.0
        self.Torque_right = 0.0
        self.Torque_Total = 0.0

        self.Power = 0.0

        self.Power_Total = 0.0
        self.Power_Left = 0.0
        self.Power_Right = 0.0

        self.CrankAngle = 0.0

        self.Cadence = 0.0
        self.Cadence_AVG = 0.0      # My calculated Cadence

        self.Balance_Left = 0.0
        self.Balance_Right = 0.0

        self.Torque_Efficiency_Left = 0.0
        self.Torque_Efficiency_Right =  0.0

        self.Pedal_Smoothness_Left = 0.0
        self.Pedal_Smoothness_Right = 0.0