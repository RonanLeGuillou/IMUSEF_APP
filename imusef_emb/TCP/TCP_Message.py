

class TCP_Message(object):

    # Invalid Command
    CMD_NO_MESSAGE = "CMD_NO_MESSAGE"

    # Commands: TCP-Client -> IMUSEF
    CMD_GET_STIM_PARAMS = "CMD_GET_STIM_PARAMS"
    CMD_SET_STIM_PARAMS = "CMD_SET_STIM_PARAMS"

    CMD_GET_SETTINGS = "CMD_GET_SETTINGS"
    CMD_SET_SETTINGS = "CMD_SET_SETTINGS"

    CMD_GET_CONTROLLER_PARAMS = "CMD_GET_CONTROLLER_PARAMS"
    CMD_SET_CONTROLLER_PARAMS = "CMD_SET_CONTROLLER_PARAMS"

    CMD_SET_TEST_STIMULATION = "CMD_SET_TEST_STIMULATION"

    CMD_SET_STIMULATION_INTENSITY = "CMD_SET_STIMULATION_INTENSITY"

    CMD_CALIBRATE_SYSTEM = "CMD_CALIBRATE_SYSTEM"
    CMD_STOP_SYSTEM = "CMD_STOP_SYSTEM"

    CMD_START_RECORD = "CMD_START_RECORD"
    CMD_STOP_RECORD = "CMD_STOP_RECORD"

    CMD_ADD_COMMENT = "CMD_ADD_COMMENT"

    CMD_RESET_CYCLING_COMPUTER = "CMD_RESET_CYCLING_COMPUTER"

    CMD_APPLY_TESTBURST = "CMD_APPLY_TESTBURST"

    CMD_BIODEX_CHANGE_SIDE = "CMD_BIODEX_CHANGE_SIDE"
    CMD_BIODEX_CALIBRATE_KNEEANGLE = "CMD_BIODEX_CALIBRATE_KNEEANGLE"

    # Command Response: IMUSEF -> TCP-Client
    CMD_RE_GET_STIM_PARAMS = "CMD_RE_GET_STIM_PARAMS"
    CMD_RE_SET_STIM_PARAMS = "CMD_RE_SET_STIM_PARAMS"

    CMD_RE_SETTINGS = "CMD_RE_SETTINGS"
    CMD_RE_CONTROLLER_PARAMS = "CMD_RE_CONTROLLER_PARAMS"

    CMD_RE_START_RECORD = "CMD_RE_START_RECORD"
    CMD_RE_STOP_RECORD = "CMD_RE_STOP_RECORD"

    CMD_RE_APPLY_TESTBURST = "CMD_RE_APPLY_TESTBURST"


    def __init__(self):

        self.CMD = TCP_Message.CMD_NO_MESSAGE;
        self.DATA = "";

    def parseFromString(self, message_str):

        data = message_str.split("@")

        if len(data) > 1:
            self.CMD = data[0];
            self.DATA = data[1]
        else:
            self.CMD = TCP_Message.CMD_NO_MESSAGE
            self.DATA = message_str


    def buildMessage(self, CMD, data):

        self.CMD = CMD;
        self.DATA = data

    def toString(self):
        return self.CMD + "@" + self.DATA




