# -*- coding: utf-8 -*-
"""
Module to simplify the handeling of the GPIO

Functionality:	# Controlling Beep (Buzzer)
				# Reading Left Button
				# Reading Right Button
				# Reading Boost Button
				# Reading Channel Z of Encoder
				# Reading of Intensity-Controller


"""

# IMPORTS
import threading
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = False


class GPIO_Manager(object):

    def __init__(self, exit_Event, RelayBox_active = False):

        self.__exit_Event = exit_Event

        # Settings

        # Relay Card
        self.__RelayBox_active = RelayBox_active;
        self.__CH_active = [False, False, False, False, False, False, False, False]
        self.__port_Relay_Ch = [26, 19, 13, 6, 5, 11, 9, 10]

        self.__port_System_LED = 14

        self.__port_Buzzer = 21
        self.__port_BOOST_Button = 17

        self.__port_LEFT_Button = 22
        self.__port_RIGHT_Button = 27

        self.__port_CrankAngle_Encoder_CHZ = 24

        self.__port_SPEED = 23
        self.__port_SWITCH_MAN_AUTO = 18

        if self.__RelayBox_active:
            self.__port_Emergency_Button = 7
        else:
            self.__port_Emergency_Button = 15

        self.__port_DEBUG_PIN = 25



        # Speed
        self.SPEED = True
        self.__lastSpeedTimstamp = 0.0
        self.__minSpeedPeriode = 0.0    # [s] ~36 km/h max Speed



        # Init GPIO
        global GPIO

        if GPIO == False:
            print("ERROR: Module <myGPIO> is not available!")
            return

        GPIO.setmode(GPIO.BCM) 											# Broadcom pin-numbering scheme
        GPIO.setwarnings(False)

        # Setup System LED
        GPIO.setup(self.__port_System_LED, GPIO.OUT)
        GPIO.output(self.__port_System_LED, GPIO.LOW)  # SYSTEM_LED OFF

        # Setup Relay Outputs
        GPIO.setup(self.__port_Relay_Ch[0], GPIO.OUT)
        GPIO.setup(self.__port_Relay_Ch[1], GPIO.OUT)
        GPIO.setup(self.__port_Relay_Ch[2], GPIO.OUT)
        GPIO.setup(self.__port_Relay_Ch[3], GPIO.OUT)
        GPIO.setup(self.__port_Relay_Ch[4], GPIO.OUT)
        GPIO.setup(self.__port_Relay_Ch[5], GPIO.OUT)
        GPIO.setup(self.__port_Relay_Ch[6], GPIO.OUT)
        GPIO.setup(self.__port_Relay_Ch[7], GPIO.OUT)

        GPIO.output(self.__port_Relay_Ch[0], GPIO.HIGH)  # Relay OFF
        GPIO.output(self.__port_Relay_Ch[1], GPIO.HIGH)  # Relay OFF
        GPIO.output(self.__port_Relay_Ch[2], GPIO.HIGH)  # Relay OFF
        GPIO.output(self.__port_Relay_Ch[3], GPIO.HIGH)  # Relay OFF
        GPIO.output(self.__port_Relay_Ch[4], GPIO.HIGH)  # Relay OFF
        GPIO.output(self.__port_Relay_Ch[5], GPIO.HIGH)  # Relay OFF
        GPIO.output(self.__port_Relay_Ch[6], GPIO.HIGH)  # Relay OFF
        GPIO.output(self.__port_Relay_Ch[7], GPIO.HIGH)  # Relay OFF

        # Setup Buzzer
        self.__duration_Beep = 0.02
        self.__duration_break_Beep = 0.02
        self.__mode_Beep = 0
        self.__event_Beep = threading.Event()
        GPIO.setup(self.__port_Buzzer, GPIO.OUT) 							# Pin set as output
        GPIO.output(self.__port_Buzzer, GPIO.LOW) 							# Pin set as low (no sound)
        thread_Beep = threading.Thread(name='BEEP_Thread', target = self.__thread_Beep_function, args = ())
        thread_Beep.start()

        # Emergency-Button
        if self.__RelayBox_active:
            GPIO.setup(self.__port_Emergency_Button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pin set as input
        else:
            GPIO.setup(self.__port_Emergency_Button, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Pin set as input

        # BOOST-Button
        GPIO.setup(self.__port_BOOST_Button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pin set as input

        # LEFT-Button
        GPIO.setup(self.__port_LEFT_Button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pin set as input

        # RIGHT-Button
        GPIO.setup(self.__port_RIGHT_Button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pin set as input

        # MAN-AUTO-Switch
        GPIO.setup(self.__port_SWITCH_MAN_AUTO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pin set as input

        # SPEED
        GPIO.setup(self.__port_SPEED, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pin set as input
        GPIO.add_event_detect(self.__port_SPEED, GPIO.RISING, callback=self.__SPEED_callback, bouncetime=250)

        # DEBUG PIN
        GPIO.setup(self.__port_DEBUG_PIN, GPIO.OUT)  # Pin set as output

        # Setup Encoder
        self.__SetZero = False
        GPIO.setup(self.__port_CrankAngle_Encoder_CHZ, GPIO.IN)#, pull_up_down=GPIO.PUD_DOWN)  # Pin set as input
        GPIO.add_event_detect(self.__port_CrankAngle_Encoder_CHZ, GPIO.RISING, callback=self.__ENCODER_Channel_Z_callback)


    # Updates the activity of relays
    def updateChannels(self, active_channels, StimFlag = False):

        # Set DebugPin
        self.setDEBUG_PIN(StimFlag)

        # Set relais
        for i in range(8):
            if not (self.__CH_active[i] == active_channels[i]):

                # Update channel
                if active_channels[i]:
                    GPIO.output(self.__port_Relay_Ch[i], GPIO.LOW)	# Relay ON
                else:
                    GPIO.output(self.__port_Relay_Ch[i], GPIO.HIGH)	# Relay OFF

        self.__CH_active = active_channels[:] # A copy is needed here



        return True


    # Creates a single Beep
    def Beep(self, duration = 0.02):
        self.__duration_Beep = duration
        self.__mode_Beep = 0
        self.__event_Beep.set();

    # Creates a double Beep
    def DoubleBeep(self, duration = 0.02, duration_break = 0.1):
        self.__duration_Beep = duration
        self.__duration_break_Beep = duration_break
        self.__mode_Beep = 1
        self.__event_Beep.set();

    # Thread function to be executed from the Beep-Thread
    def __thread_Beep_function(self):
        global GPIO

        if GPIO==False:
            print("No GPIO. Closing audio cue thread.")
            return

        while not self.__exit_Event.isSet():

            # Wait for Event to happen
            self.__event_Beep.wait(0.5)

            # Do the Beep
            if self.__event_Beep.isSet():

                if self.__mode_Beep == 0:
                    GPIO.output(self.__port_Buzzer, GPIO.HIGH)
                    time.sleep(self.__duration_Beep)
                    GPIO.output(self.__port_Buzzer, GPIO.LOW)
                elif self.__mode_Beep == 1:
                    GPIO.output(self.__port_Buzzer, GPIO.HIGH)
                    time.sleep(self.__duration_Beep)
                    GPIO.output(self.__port_Buzzer, GPIO.LOW)
                    time.sleep(self.__duration_break_Beep)
                    GPIO.output(self.__port_Buzzer, GPIO.HIGH)
                    time.sleep(self.__duration_Beep)
                    GPIO.output(self.__port_Buzzer, GPIO.LOW)

                self.__event_Beep.clear()

        # Clean up after exit
        GPIO.cleanup()



    # Returns the State of the Emergency Button
    # - 0: Emergency Button is pressed
    # - 1: Emergency Button not pressed
    def getButton_Emergency(self):

        state = GPIO.input(self.__port_Emergency_Button)

        if self.__RelayBox_active:
            if state:
               return 0
            else:
                return 1
        else:
            if state:
               return 1
            else:
                return 0

    # Returns the State of the BOOST Button
    # - True: Button is pressed
    # - False: Button not pressed
    def getButton_BOOST(self):

        return GPIO.input(self.__port_BOOST_Button)

    # Returns the State of the LEFT Button
    # - True: Button is pressed
    # - False: Button not pressed
    def getButton_LEFT(self):

        return  GPIO.input(self.__port_LEFT_Button)

    # Returns the State of the RIGHT Button
    # - True: Button is pressed
    # - False: Button not pressed
    def getButton_RIGHT(self):

        return GPIO.input(self.__port_RIGHT_Button)

    # Returns the State of the MAN_AUTO Switch
    # - True: Switch is ON
    # - False: Switch is OFF
    def getSwitch_MAN_AUTO(self):

        return GPIO.input(self.__port_SWITCH_MAN_AUTO)



    # Executes actions after receiving an event from Encoder Channel Z
    def __ENCODER_Channel_Z_callback(self, channel):

        # Reset Counter
        self.__SetZero = True
        #self.Beep()

    def getSpeedTimeStamp(self):
        return self.__lastSpeedTimstamp

    # Executes actions after receiving an event from Encoder Channel Z
    def __SPEED_callback(self, channel):

        if self.__lastSpeedTimstamp == 0.0:
            self.__lastSpeedTimstamp = time.time()
        else:
            now = time.time()

            if(now - self.__lastSpeedTimstamp) > self.__minSpeedPeriode:
                self.__lastSpeedTimstamp = now

        # if (self.SPEED == False):
        #     return
        #
        # self.SPEED = False
        # self.__lastSpeedTimstamp = time.time()
        # time.sleep(self.__minSpeedPeriode)
        #
        # self.SPEED = True
        # self.Beep()


    # Returns whether to reset the crank-angle or not
    def ResetCrankAngle(self):

        if(self.__SetZero):
            self.__SetZero = False
            return True
        else:
            return False


    # Set´s or clears the output of the Debug-Pin
    def setDEBUG_PIN(self, set_pin):

        if set_pin:
            GPIO.output(self.__port_DEBUG_PIN, 1)
        else:
            GPIO.output(self.__port_DEBUG_PIN, 0)


    # Sets the System LED to indicate that the system is ready
    def setSystemLED(self, set_LED):
        if set_LED:
            GPIO.output(self.__port_System_LED, 1)
        else:
            GPIO.output(self.__port_System_LED, 0)



### Main Programm
if __name__ == '__main__':
    event_exit = threading.Event()
    mygpio = GPIO_Manager(event_exit)

    mygpio.DoubleBeep()

    try:
        while True:

            print("CrankAngle: " + str(mygpio.CrankAngle))
            time.sleep(0.01)
    except KeyboardInterrupt:
        print('\nUser requested Application STOP\n')
        event_exit.set()
