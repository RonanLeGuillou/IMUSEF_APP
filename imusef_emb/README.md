# IMUSEF [WORK IN PROGRESS]

The IMUSEF Project is the follow up of the GonioCycle project (IMU based control of FES cycling), mainly developped by B.SIJOBERT.

This project aims to facilitate usage, diffusion and scaling, through a completely modular architecture.


The observer module is not currently integrated as a module and has to be placed in the root folder of this project. 
You might need to add the following export so that the odepack library is found during import of the CPG part :
~~~bash 
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:./observer/Common_Lib/odepack/obj/
~~~


The only necessary library is SENSBiotk. Optionnal modules and libraries include Adafruit_BNO055 for the IMUs, RPI.GPIO 
for audio cueing, as well as Feetme, BerkelStim and Pytrainer APIs.

If you do not have access to the Feetme, BerkelStim and Pytrainer API modules, please comment out the import lines at 
the start of the main script IMUSEF.py.

# Automatic startup

Rather than starting the IMUSEF.py script, it is preferable to start watchdog_IMUSEF.py, taking care automatically of 
starting, monitoring and if necessary restarting IMUSEF.py.

To start this program automatically at start-up of the platform in order to work in headless mode, complete the next few
 steps to setup this program as a service.
1.  Ensure that the paths used in the file "watchdog_IMUSEF.service" at the desired ones.
2.  Move or copy the file "watchdog_IMUSEF.service" to the following location : 
**_/lib/systemd/system/watchdog_IMUSEF.service_**
    ~~~bash 
    sudo cp ./watchdog_IMUSEF.service /lib/systemd/system/watchdog_IMUSEF.service
    ~~~
3.  To reload the services, execute the command : 
    ~~~bash 
    sudo systemctl daemon-reload
    ~~~
4.  Then validate and enable the new service to include it in the startup routine with the command :
    ~~~bash 
    sudo systemctl enable watchdog_IMUSEF.service
    ~~~
5.  Check the status of the service and make sure it is loaded and no error message is present :
    ~~~bash 
    sudo systemctl -l status watchdog_IMUSEF.service
    ~~~
6.  Done. This service will now be executed every time the system boots-up. 

7.  Optional : If you only want to automatically start IMUSEF during start-up but you don´t want to automatically restart it after an error 
     please comment the following lines in the <watchdog_IMUSEF.service> file:
    ~~~bash 
    # Restart=on-failure
    # RestartSec=2
    ~~~
    Make sure to repeat step 2 after performing any change in this file.

8.  Optional : To deactivate/activate the watchdog service during development use following commands:
    
    - DEACTIVATE
    ~~~bash 
    sudo systemctl disable watchdog_IMUSEF.service
    sudo reboot
    ~~~
    
    - ACTIVATE
    ~~~bash 
    sudo systemctl enable watchdog_IMUSEF.service
    sudo reboot
    ~~~


