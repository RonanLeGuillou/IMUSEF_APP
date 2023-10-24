#!/usr/bin/env python

import signal
import psutil
import subprocess
import time
import sys
import os

DEBUG = False


# Define Python user-defined exceptions
class Error(Exception):
    """Base class for exceptions in this module."""
    pass


# Define Python user-defined TimeoutError exception
class TimeoutError(Error):
    """Exception raised when the timeout is reached"""
    def __init__(self):
        super(TimeoutError, self).__init__()
        self.message = "TIMEOUT"


# Define callback function raising the user-defined Python TimeoutError exception
def Callback_TimeoutError(signum, frame):
    if DEBUG: print("RAISING TIMEOUT INTERRUPT ")
    raise TimeoutError()


# Function designed to wrap an interrupt handling system around a blocking call to allow a Timeout feature
def run_func_on_timeout(timeout, default, func, *args, **kwargs):
    # If no timeout specified, execute the function normally, passing the args
    if not timeout:
        return func(*args, **kwargs)
    # Otherwise :
    # Setting the timeout callback handler to be triggered by the alarm signal.
    signal.signal(signal.SIGALRM, Callback_TimeoutError)
    # The callback function will be called if signal.alarm is not disabled before timeout runs out.
    signal.alarm(timeout)
    # Starting the function under a try/except/finally wrapper to allow the alarm to
    # raise its interrupt and catch it during the blocking function.
    try:
        result = func(*args, **kwargs)
    # If TimeoutError, set result to the given default value.
    except TimeoutError as err:
        result = default
        if DEBUG: print('TimeoutError Error caught. Message is :', err.message)
    # If IOError, set result to the given default value.
    # Error typical of target crash, leaving the piped stdout connection damaged.
    except IOError as err:
        result = default
        if DEBUG: print('IOError Error caught. Message is :', err.message)
    # Finally, in any case, disable and cancel the alarm.
    finally:
        signal.alarm(0)
    return result


# Kill target process and any existing children.
def kill_process_and_children(parent_pid, sig=signal.SIGTERM):
    # If possible, retrieve the process corresponding to the given pid.
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        print("NoSuchProcess")
        return
    # Retrieve potential children of the given process.
    children = parent.children(recursive=True)
    # For each of them, try to kill them.
    for process in children:
        if DEBUG: print(process)
        try:
            process.send_signal(sig)
        except psutil.NoSuchProcess as err:
            if DEBUG: print("NoSuchProcess :", err)  # Already dead.

    # Finally, kill the given parent process.
    parent.send_signal(sig)
    if DEBUG: print("Target process killed")


# Open target script in an independent process and redirect its standard output to be caught and readable here.
def start_python_script(script='IMUSEF.py'):
    if DEBUG: print("Starting target python script\n")
    # Starting the desired python script and redirect its standard outputs (stdout) to the created process.
    # The use of GNU "screen" session multiplexing is unfortunately incompatible with stdout redirection.
    # First argument : python,
    # Second argument : script name,
    # Third argument : True (flag which should be used by the script as a request to send regular KEEPALIVE prints).
    process = subprocess.Popen(['python', script, 'True'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               shell=False)
    return process


# Main WATCHDOG class creating, handling, monitoring and if necessary restarting the desired script.
class Watchdog:
    def __init__(self, timeout=2, start_time_margin=2, script_folder='', script_name='IMUSEF.py'):
        # Setting up given arguments as member parameters.
        self.timeout = timeout
        self.TimeStamp_last_KEEPALIVE_SIGNAL = None
        # Figuring out the path to the target script.
        self.script_folder = script_folder
        self.script_name = script_name
        self.script_path = self.script_folder+self.script_name
        if DEBUG: print("self.script_path :",self.script_path)

        # Monitored script process information
        self.process = None
        self.process_pid = None
        if DEBUG: print("Watchdog initialized")

        # Define amount of time allowed to the target process to start-up properly before being restarted
        self.start_time_margin = start_time_margin
        self.start_time = time.time()
        # Flag allowing to discriminate between start-up waiting delay
        # or if the process stopped sending keepalive signals
        self.FLAG_process_was_ready = False

    # Main run method with an infinite loop
    def run(self):
        # Create the process to monitor
        if DEBUG: print("Watchdog Run started")
        self.process = start_python_script(script=self.script_path)
        self.process_pid = self.process.pid
        self.start_time = time.time()
        # time.sleep(0.25)

        # Main loop reading the redirected stdout from the process and checking for KEEPALIVE_SIGNAL
        if DEBUG: print("Watchdog While loop started")
        while True:
            # Trying to read the pipe to the process. If result is "default", Timeout has occurred.
            # if DEBUG: print("Reading a new line.")
            line = run_func_on_timeout(timeout=self.timeout, default=None, func=self.process.stdout.readline)
            # If direct Timeout occurred, check restart conditions to restart the script or go back to waiting.
            if line is None:
                # If the process was previously sending KEEPALIVE_SIGNAL, restart it.
                if self.FLAG_process_was_ready:
                    if DEBUG: print("Timeout reached and was previously alive and kicking. Restarting IMUSEF")
                    self.restart_python_script()
                # Otherwise, if it never started-up properly, and start_time_margin has passed, restart it.
                elif time.time() > self.start_time + self.start_time_margin:
                    if DEBUG: print("Start-up deadline start_time_margin reached. Restarting IMUSEF")
                    self.restart_python_script()
                # Otherwise, wait until start-up completes or start_time_margin is passed.
                else:
                    if DEBUG: print("Waiting start_time_margin for the process to start-up properly.")
                    pass

            # Otherwise, a valid line was retrieved from the process.
            # If the line retrieved is KEEPALIVE_SIGNAL,
            # continue without displaying to avoid flooding the console.
            elif line.rstrip() == 'KEEPALIVE_SIGNAL':
                # if DEBUG: print("KEEPALIVE_SIGNAL REFRESHED\r")

                # If first KEEPALIVE_SIGNAL, consider the target process start-up as completed.
                if not self.FLAG_process_was_ready:
                    if DEBUG: print("First KEEPALIVE_SIGNAL received. Considered alive.")
                    if DEBUG: print("Target process took ", time.time() - self.start_time,
                                    "seconds to send its first KEEPALIVE_SIGNAL")
                    # Target process now has to keep sending KEEPALIVE_SIGNAL
                    self.FLAG_process_was_ready = True
                # First or not, most recent KEEPALIVE_SIGNAL is now.
                self.TimeStamp_last_KEEPALIVE_SIGNAL = time.time()

            # If the line retrieved was anything else, display it to console
            else:
                sys.stdout.write(line)
                sys.stdout.flush()
                # If the process was previously ready but the last KEEPALIVE_SIGNAL was NOT received
                # in the given Timeout time frame, restart the target process.
                if self.FLAG_process_was_ready:
                    if time.time() > self.TimeStamp_last_KEEPALIVE_SIGNAL + self.timeout:
                        if DEBUG: print("Timeout deadline for new KEEPALIVE_SIGNAL reached. Restarting IMUSEF")
                        self.restart_python_script()

    # Restart method killing the target process, preparing for restart, and restarting the target process
    def restart_python_script(self):
        print("Restarting IMUSEF due to TIMEOUT considered as crash")
        # KILLING IMUSEF
        kill_process_and_children(parent_pid=self.process_pid)
        # Reset the deadline check process parameters
        self.FLAG_process_was_ready = False
        self.TimeStamp_last_KEEPALIVE_SIGNAL = None
        # RESTARTING IMUSEF
        self.process = start_python_script(script=self.script_path)
        self.process_pid = self.process.pid
        # Reset the process start_time
        self.start_time = time.time()
        if DEBUG: print("IMUSEF RESTARTED")


if __name__ == '__main__':
    # If problems with path to launch your script, add pathname as target script_folder to the Watchdog.
    # pathname = os.path.dirname(sys.argv[0])+'/'
    # print 'Current watchdog working directory: %s' % (os.getcwd())
    IMUSEF_WATCHDOG = Watchdog(timeout=1, start_time_margin=3, script_folder='', script_name='IMUSEF.py')
    if DEBUG: print("\n STARTING IMUSEF_WATCHDOG\n")
    # Run the Watchdog main loop.
    IMUSEF_WATCHDOG.run()
