# IMPORTS
import socket
import threading
import time
from TCP_Message import TCP_Message
from queue import Queue
from random import randrange
import socket
import sys



class TCP_Server(object):

    NOT_CONNECTED = -1;
    LISTENING = 0;
    CONNECTED = 1;

    def __init__(self, port):

        # DataContainer
        self.__sendingQueue = Queue()
        self.__receiveQueue = Queue()

        # Settings
        self.__ReceiveBufferSize = 1024
        self.__TCP_port = port

        # Connection Variables
        self.STATE = TCP_Server.NOT_CONNECTED
        self.__reconnect = False;


    # Working Thread to ensure Connection, performs automatic reconnect if connection is lost
    def __Connecting_Worker(self, exit_Event):

        # Main - Loop
        while not exit_Event.isSet():

            # If not connected
            if self.STATE == TCP_Server.NOT_CONNECTED:

                # Clear up old things
                try:
                    self.__connection.close()
                except Exception as e:
                    #print ("Closing Error:" ,e)
                    pass

                # Try to connect
                self.STATE = TCP_Server.LISTENING

                while not exit_Event.isSet() and self.STATE == TCP_Server.LISTENING:

                    try:
                        if not self.__reconnect:
                            # Create a TCP/IP socket
                            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                            # Bind the socket to the address given
                            server = ('', self.__TCP_port)
                            self.__sock.bind(server)

                            self.__reconnect = True

                        self.__sock.listen(1)

                        # Waiting for Client
                        print('Waiting for Client')
                        self.__connection, self.Client = self.__sock.accept()

                        # Found somebody to play with
                        print('Client connected:', self.Client)

                        self.STATE = TCP_Server.CONNECTED;

                    except Exception as error:
                       print("Error during Connecting:", error)
                       self.__sock.close()
                       time.sleep(1)


            time.sleep(0.5);



    # Puts a new String into the Sending Queue to be processed
    def sendData(self, data):

        if (self.STATE == TCP_Server.NOT_CONNECTED):
            return;

        self.__sendingQueue.put(data)

    # Returns the first message String of the sending Queue. If there is no data, "" is returned
    def getMessage(self):

        try:
            return self.__receiveQueue.get(False)
        except Exception as e:
            return ""

    # Informs wheter there is data received from the client
    def hasData(self):

        if not (self.STATE == TCP_Server.CONNECTED):
            return  False;
        else:
            return not self.__receiveQueue.empty()


    # Doing the work, sends data if there is some. Otherwise just waiting
    def __Sending_Worker(self, exit_Event):

       while not exit_Event.isSet():

            if self.STATE == TCP_Server.CONNECTED:
                try:
                    # Get message to send
                     message = self.__sendingQueue.get(True, 0.5)

                     self.__connection.sendall(message)

                except Exception as e:
                    #print(e)
                    pass
            else:
                time.sleep(0.1)

    # Doing the work, sends data if there is some. Otherwise just waiting
    def __Receiving_Worker(self, exit_Event):

        # Main Loop for Receiving
        while not exit_Event.isSet():

            if(self.STATE == TCP_Server.CONNECTED):
               try:
                data = self.__connection.recv(self.__ReceiveBufferSize)

                # Client said good bye
                if data =="":
                    raise Exception

                else:
                    self.__receiveQueue.put(data)
                    print("Received: " + data)

               except Exception as error:
                   #print("Receiving error", error)
                   print("Connection to Client lost!!!")
                   self.STATE = TCP_Server.NOT_CONNECTED
            else:
                time.sleep(0.1)



    # Starts the Server in order to find a client
    def start(self, exit_Event):

        # Start Connecting Thread
        self.__thread_Connecting_Worker = threading.Thread(name='TCP_Connenction_Thread', target=self.__Connecting_Worker, args=(exit_Event,))
        self.__thread_Connecting_Worker.daemon = True
        self.__thread_Connecting_Worker.start()

        # Starting Thread
        self.__thread_Receiving_Worker = threading.Thread(name='TCP_Receiving_Thread', target=self.__Receiving_Worker, args=(exit_Event,))
        self.__thread_Receiving_Worker.daemon = True
        self.__thread_Receiving_Worker.start()

        # Start Sending Thread
        self.__thread_Sending_Worker = threading.Thread(name='TCP_Sending_Thread', target=self.__Sending_Worker, args=(exit_Event,))
        self.__thread_Sending_Worker.daemon = True
        self.__thread_Sending_Worker.start()

    def stop(self):
        try:
            self.__connection.close()
            self.__sock.close()
        except Exception as error:
            #Ignore for now
            pass


if __name__ == '__main__':

    e = threading.Event()
    myTCPServer = TCP_Server(12346)
    myTCPServer.start(e)


    i = 0
    try:
        while True:


            i+=1
            if myTCPServer.STATE == TCP_Server.CONNECTED:
                print(str(i) + ") Working")

                myTCPServer.sendData(str(randrange(10)))

                # Did we receive some data?
                while myTCPServer.hasData():
                    msg = myTCPServer.getMessage()

                    print(str(myTCPServer.Client) + ": "+msg);

            elif myTCPServer.STATE == TCP_Server.LISTENING:
                print("Waiting for Client")
            else:
                print("No connection: Trying to connect")

            time.sleep(1)


    except KeyboardInterrupt:
       print("KEYBOARD INTERRUPT")

    e.set()



    print("All good now");





