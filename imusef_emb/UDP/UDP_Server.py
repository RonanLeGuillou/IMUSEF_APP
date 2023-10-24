# IMPORTS
import socket
import threading
import time
from queue import Queue
from random import randrange


DEBUG = False

class UDP_Server(object):

    def __init__(self, port):

        # DataContainer
        self.__sendingQueue = Queue()

        # Setup a new UDP_Server Socket just for sending
        self.__UDP_Port = port
        self.__BROADCAST_IP = '192.168.4.255'
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # # TODO: Morten TEst
        # self.__UDP_Port2 = 12340
        # self.__BROADCAST_IP2 = '192.168.4.255'
        # self.__server2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # self.__server2.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST2, 1)

    # Starts a the working Thread
    def start(self, exit_Event):
        # Starting Thread
        self.__thread_Worker = threading.Thread(name='UDP_Sending_Thread', target=self.__Worker_Method, args=(exit_Event, ))
        self.__thread_Worker.daemon = True
        self.__thread_Worker.start()

    # Puts a new String into the Sending Queue to be processed
    def sendData(self, data):
        self.__sendingQueue.put(data)


    # Doing the work, sends data if there is some. Otherwise just waiting
    def __Worker_Method(self, exit_Event):

       while not exit_Event.isSet():

            try:
                # Get message to send
                message = self.__sendingQueue.get(True, 0.5)
                self.__server.sendto(message, (self.__BROADCAST_IP, self.__UDP_Port))
                #self.__server.sendto(message, (self.__BROADCAST_IP, 12340))
            except Exception as e:
                if DEBUG: print(e)
                pass



if __name__ == '__main__':

    e = threading.Event()
    myUDPServer = UDP_Server(e)

    i = 0
    try:
        while True:
            i+=1
            print(str(i) + ") Working")

            myUDPServer.sendData(str(randrange(10)))
            time.sleep(0.1)


    except KeyboardInterrupt:
        e.set()





