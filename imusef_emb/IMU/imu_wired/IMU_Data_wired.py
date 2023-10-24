
class IMU_Data_wired(object):

    def __init__(self):

        # IMU_TimeStamp: TODO: Only needed for Observer-> Do not use elsewhere
        self.IMU_timestamp = 0;

        # Wired IMU Data
        self.leftKneeAngle = 0.0;
        self.rightKneeAngle = 0.0;

        self.leftThighAngle = 0.0;
        self.rightThighAngle = 0.0;

        self.gx = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self.gy = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self.gz = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}

        self.ax = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self.ay = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self.az = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
