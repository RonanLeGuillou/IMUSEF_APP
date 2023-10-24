#! /usr/bin/env python

#import subprocess
#import sys


#try:
#    status_imu = subprocess.call("./imu_dump_full.py" + " -o data_imu.txt", shell=True)    
#    if status_imu < 0:
#        print >>sys.stderr, "Child was terminated by signal", -status_imu
#    else:
#        print >>sys.stderr, "Child returned", status_imu
#except OSError as e:
#    print >>sys.stderr, "Execution failed:", e

#try:
#    status_ptap = subprocess.call("/home/cybathlon/Bureau/Cybathlon/ant/openant-master/examples/powertap_p1.py", shell=True)      
#    if status_ptap < 0:
#        print >>sys.stderr, "Child was terminated by signal", -status_ptap
#    else:
#        print >>sys.stderr, "Child returned", status_ptap
#except OSError as e:
#    print >>sys.stderr, "Execution failed:", e

import imu_dump_full

 

#def launch_stream_ptap():   
##    execfile('/home/cybathlon/Bureau/Cybathlon/ant/openant-master/examples/powertap_p1.py')
#    try:
#        status_ptap = subprocess.call("/home/cybathlon/Bureau/Cybathlon/ant/openant-master/examples/powertap_p1.py", shell=True)      
#        if status_ptap < 0:
#            print >>sys.stderr, "Child was terminated by signal", -status_ptap
#        else:
#            print >>sys.stderr, "Child returned", status_ptap
#    except OSError as e:
#        print >>sys.stderr, "Execution failed:", e
#
#def launch_stream_imu():
#    try:
#        status_imu = subprocess.call("./imu_dump_full.py" + " -o data_imu.txt", shell=True)    
#        if status_imu < 0:
#            print >>sys.stderr, "Child was terminated by signal", -status_imu
#        else:
#            print >>sys.stderr, "Child returned", status_imu
#    except OSError as e:
#        print >>sys.stderr, "Execution failed:", e
    
def main():
#    thread_ptap = threading.Thread(None, target = launch_stream_ptap)
#    thread_imu = threading.Thread(None, target = launch_stream_imu)
#    
#    thread_ptap.start()
#    thread_imu.start()
    imu_dump_full.main
    imu_dump_full
    print('lance')
    
if __name__ == "__main__":
    main()